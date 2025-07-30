import os
import concurrent
import numpy as np
import scipy
from .ndarray_shifted import ndarray_shifted
from .utils import blit, invert_function_numerical, image_is_label
import threadpoolctl

# TODO:
# - implement posttransforms, allowing the unfitted transform to be on the left hand side

def rotation_matrix(z, y, x):
    """Perform *clockwise* rotation in degrees along the three axes"""
    sin = lambda x : np.sin(np.deg2rad(x))
    cos = lambda x : np.cos(np.deg2rad(x))
    zy_rotation = lambda theta : \
        np.asarray([[cos(theta), sin(theta), 0],
                    [-sin(theta), cos(theta), 0],
                    [0, 0, 1]])
    yx_rotation = lambda theta : np.roll(zy_rotation(theta), 1, axis=(0,1))
    xz_rotation = lambda theta : np.roll(zy_rotation(theta), -1, axis=(0,1))
    return yx_rotation(z) @ xz_rotation(y) @ zy_rotation(x)


class Transform:
    """Base class for all transforms.

    To use, instantiate and then call fit().

    Conceptually, there are two types of transforms: those that use points (see
    PointTransform) and those that don't.  Parameters can either be definitions
    of the transform (e.g., z-shift) or they can be hyperparameters (e.g., a
    smoothness regularizser).  They should be floats or booleans, and can be set
    through the GUI.

    Required method to subclass is : "_transform" (map points from base space to
    the new space), and "invert" (the opposite).  If parameters need to be
    calculated from the points, also define _fit (takes points_start and
    points_end and modifies the current object).  If you can't define "invert",
    then subclass TransformPointsNoInverse instead, which will create one for
    you numerically.

    If you want parameters to be accepted by the constructor, use the
    "DEFAULT_PARAMETERS" dict, where the key is the name and the value is the default.
    They will be saved in self.params.  This is NOT for parameters which need to
    be fit or can be reconstructed perfectly from points_start and points_end.

    There are a few final rules that must be followed when implementing new
    Transforms:

    1. The transform MUST be able to be reconstructed perfectly from the output of the __repr__ function.

    """
    NAME = ""
    SHORTCUT_KEY = ""
    SORT_WEIGHT = 0 # How to sort when listing all transforms
    DEFAULT_PARAMETERS = {}
    GUI_DRAG_PARAMETERS = [None, None, None]
    def __init__(self, **kwargs):
        # Initialise parameters to either pass values or defaults
        self.params = {}
        for k in self.DEFAULT_PARAMETERS.keys():
            self.params[k] = kwargs[k] if k in kwargs else self.DEFAULT_PARAMETERS[k]
        # Check for invalid arguments
        for k in kwargs.keys():
            assert k in self.DEFAULT_PARAMETERS.keys(), f"Keyword argument {k} is not valid for the transform {type(self)}, instead try {list(self.DEFAULT_PARAMETERS.keys())}"
        # If this transform needs to be fit, then fit it.
        if hasattr(self, "_fit"):
            self._fit()
    def __repr__(self):
        ret = self.__class__.__name__
        ret += "("
        parts = []
        for k,v in self.params.items():
            parts.append(f"{k}={v}")
        ret += ", ".join(parts)
        ret += ")"
        return ret
    def __eq__(self, other):
        return repr(self) == repr(other)
    def __add__(self, other):
        return compose_transforms(self, other)
    def __call__(self, data, *args, **kwargs):
        adata = np.asarray(data)
        if (adata.ndim == 2 and adata.shape[1] == 3) or (adata.ndim == 1 and adata.shape[0] == 3):
            return self.transform(adata, *args, **kwargs)
        return self.transform_image(adata, *args, **kwargs)
    def save(self, filename):
        with open(filename, "w") as f:
            f.write(repr(self))
    @staticmethod
    def load(filename):
        with open(filename, "r") as f:
            text = f.read()
        return eval(text, globals(), None)
    def transform(self, points):
        points = np.asarray(points)
        is_1d = False
        if points.ndim == 1:
            points = points[None]
            is_1d = True
        if 0 in points.shape: # If any dimensions don't exist, no points to transform
            return points
        assert points.shape[1] == 3, "Input points must be in volume space"
        if is_1d:
            return self._transform(points)[0]
        else:
            return self._transform(points)
    def _transform(self, points):
        """Forward mapping function for the transformation"""
        raise NotImplementedError("Please subclass and replace")
    def inverse_transform(self, points):
        """Inverse mapping function for the transformation.

        Override this function to provide a more efficient implementation.
        """
        return self.invert().transform(points)
    def invert(self):
        raise NotImplementedError("Please subclass and replace")
    def origin_and_maxpos(self, img, output_size=None, force_size=True):
        """Find an output (transformed) image bounding box.

        `img` is the input image.

        If `output_size` is None, this will generate the smallest possible
        bounding box  If it is a list or tuple of integers with length 3,
        it will generate an image of the given size.  If it is a list of tuple
        of 3 lists or tuples of length 2, it will interpret each as a minimum
        and maximum coordinate in the output space.

        If `force_size` is False, it will interpret `output_size` as a maximum
        bounding box, but it may generate a smaller image if it is more
        computationally efficient.
        """
        input_bounds = img.shape
        origin_offset = img.origin if isinstance(img, ndarray_shifted) else [0,0,0]
        corners_pretransform = [[a, b, c] for a in [0, input_bounds[0]] for b in [0, input_bounds[1]] for c in [0, input_bounds[2]]]
        corners_pretransform = (corners_pretransform) + np.asarray(origin_offset)
        if isinstance(self, PointTransform): # For nonlinear transforms a box is not enough.  This is also not enough but it is better than nothing.
            origin = np.min(np.concatenate([self.transform(corners_pretransform), self.points_end]), axis=0).astype("float32")
            maxpos = np.max(np.concatenate([self.transform(corners_pretransform), self.points_end]), axis=0).astype("float32")
        else:
            origin = np.min(self.transform(corners_pretransform), axis=0).astype("float32")
            maxpos = np.max(self.transform(corners_pretransform), axis=0).astype("float32")
        if output_size is None: # the default
            pass
        elif isinstance(output_size, (list,tuple,np.ndarray)): # Manually specifying coordinates
            maxpos_ = np.asarray([r[1] if isinstance(r, tuple) else r if r is not None else np.inf for r in output_size], dtype="float32")
            origin_ = np.asarray([r[0] if isinstance(r, tuple) else 0 if r is not None else -np.inf for r in output_size], dtype="float32")
            if force_size:
                origin = origin_
                maxpos = maxpos_
            else:
                origin = np.max([origin_, origin], axis=0)
                maxpos = np.min([maxpos_, maxpos], axis=0)
        else:
            raise ValueError(f"Invalid value of `output_size` passed: {output_size}")
        return origin,maxpos
    def transform_image(self, img, output_size=None, labels=None, force_size=True):
        """Generic non-rigid transformation for images.

        Apply the transformation to image `img`.

        If `output_size` is None, this will generate the smallest possible
        output image size.  If it is a list or tuple of integers with length 3,
        it will generate an image of the given size.  If it is a list of tuple
        of 3 lists or tuples of length 2, it will interpret each as a minimum
        and maximum coordinate in the output space.

        If `labels` is True, no interpolation is performed.  This is for images
        of labels, e.g., segmentations.  If None, it will guess whether the
        image is labels or not.

        If `force_size` is False, it will interpret `output_size` as a maximum
        bounding box, but it may generate a smaller image if it is more
        computationally efficient.

        This can be overridden by more efficient implementations in subclasses.

        """
        # First, if we have an ndarray_shifted object, shift it first with another transform.
        if isinstance(img, ndarray_shifted) and np.any(img.origin != np.asarray([0,0,0])):
            shift = TranslateFixed(z=img.origin[0], y=img.origin[1], x=img.origin[2])
            return (shift + self).transform_image(np.asarray(img), output_size=output_size, labels=labels, force_size=force_size)
        # Housekeeping
        if labels is None:
            labels = image_is_label(img)
        if img.ndim == 2:
            img = img[None]
        origin, maxpos = self.origin_and_maxpos(img, output_size=output_size, force_size=force_size)
        shape = (maxpos - origin).astype(int)
        img_offset = ndarray_shifted(img).origin
        img   = np.ascontiguousarray(img,  dtype=np.float32 if not labels else img.dtype)
        origin = origin.astype(np.float32)
        # shape = np.round(np.ceil(maxpos - origin)/downsample_output).astype(int) # Maybe this is better?
        # shape = np.asarray(img.shape).astype(int) # Pulled from old code

        if img.shape[0] == 1: # This is a hack to get around thickness=1 images disappearing in the map_coordinates function 
            img = np.concatenate([img, img])
        if img.shape[1] == 1:
            img = img*np.ones((1,2,1), dtype=img.dtype)
        if img.shape[2] == 1:
            img = img*np.ones((1,1,2), dtype=img.dtype)
        # For memory efficiency, we split coords into chunks
        zcoords = np.arange(0, shape[0], dtype="float32")
        ycoords = np.arange(0,shape[1], dtype="float32")
        xcoords = np.arange(0,shape[2], dtype="float32")
        def chunker(zcoords, ycoords, xcoords, chunksize=10_000_000):
            """It takes lots of memory to do this all at once so we create chunks based on z planes"""
            zsize = len(ycoords)*len(xcoords)
            n_z_per_chunk = np.maximum(chunksize // zsize, 1)
            single_plane = np.asarray([np.repeat(ycoords, len(xcoords)), np.tile(xcoords, len(ycoords))], dtype="float32")
            zcoords_float32 = np.asarray(zcoords, dtype="float32")
            for i in range(0, 100000):
                zfrom, zto = n_z_per_chunk*i,n_z_per_chunk*(i+1)
                if zfrom >= len(zcoords):
                    return
                if zto > len(zcoords):
                    zto = len(zcoords)
                inds = (slice(zfrom,zto), slice(None), slice(None))
                chunk_shape = (zto-zfrom, len(ycoords), len(xcoords))
                coords = np.concatenate([np.repeat(zcoords_float32[zfrom:zto], single_plane.shape[1])[None,:], np.tile(single_plane, zto-zfrom)], axis=0).T
                yield coords, chunk_shape, inds

        # First, we construct a list of coordinates of all the pixels in the
        # image, and transform them to find out which point is mapped to which
        # other point.  Then, we inverse transform them to construct a matrix of
        # mappings.  We turn this matrix of mappings into a matrix of pointers
        # from the destination image to the source image, and then use the
        # map_coordinates function to perform this mapping.
        output = np.zeros((len(zcoords),len(ycoords),len(xcoords)), dtype=(img.dtype if labels else "float32"))
        def _process_chunk(args):
            grid, chunk_shape, inds = args
            grid = grid + origin
            mapped = self.inverse_transform(grid)
            if isinstance(img, ndarray_shifted):
                mapped += img.origin
            disp = mapped.reshape(*chunk_shape, 3).transpose(3, 0, 1, 2)
            block = scipy.ndimage.map_coordinates(img, disp, prefilter=False, order=(0 if labels else 1))
            return inds, block
        with threadpoolctl.threadpool_limits(limits=1): # Parallelise here, so disable parallelisation on threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as pool:
                for inds, block in pool.map(_process_chunk, chunker(zcoords, ycoords, xcoords, chunksize=4_000_000)):
                    output[inds] = block
        return ndarray_shifted(output, origin=origin, only_if_necessary=True) # Added -origin from origin due to TranslateFixed + Rescale on a ndarray_shifted but not sure if this is the right spot
    @staticmethod
    def pretransform(*args, **kwargs):
        """Default fixed transform, applied before this transform is applied.

        This can usually be set to the Identity transformation, except when only
        part of the transform should be fit with data, for instance, composed
        transforms where only the last element is set to be fit.  This is also
        the default when the parameters for the transform have not yet been set.

        """
        return Identity()

class PointTransform(Transform):
    """Transformation based on starting and ending points

    Please define:
    - self.transform
    - self.inverse_transform
    - (Optionally) self.invert

    Guarantees access to:
    - self.points_start
    - self.points_end
    """
    def __init__(self, points_start=None, points_end=None, **kwargs):
        # Save and process the points for the transform
        points_start = np.asarray(points_start)
        points_end = np.asarray(points_end)
        assert points_start.shape == points_end.shape, "Points start and end must be the same size"
        self.points_start = points_start
        self.points_end = points_end
        super().__init__(**kwargs)
    @classmethod
    def from_transform(cls, transform, *args, **kwargs):
        """Alternative constructor which steals the points from an existing Transform object"""
        return cls(points_start=transform.points_start, points_end=transform.points_end, *args, **kwargs)
    def __repr__(self):
        ret = self.__class__.__name__
        ret += "("
        ret += f"points_start={self.points_start.tolist()}, points_end={self.points_end.tolist()}"
        for k,v in self.params.items():
            ret += f", {k}={v}"
        ret += ")"
        return ret

class AffineTransform:
    """AffineTransform should always be inherited with PointTransform

    To subclass, use the _fit function to define the parameters self.shift and
    self.matrix for the two components of the affine transform.  This defines
    all other necessary functions for a transform.  If you have multiple
    inheritance from PointTransform, you can use self.points_start and
    self.points_end.

    """
    def _transform(self, points):
        return points @ self.matrix - self.shift
    def transform_image(self, image, output_size=None, labels=None, force_size=True):
        # Optimisation for the case where no image transform needs to be
        # performed.
        if np.all(self.matrix == np.eye(3)) and ((not isinstance(image, ndarray_shifted)) or np.all(image.origin==[0,0,0])):
            if output_size is None:
                return ndarray_shifted(image, origin=-self.shift, only_if_necessary=True)
            # else:
            #     newimg = np.zeros_like(image)
            #     blit(image, newimg, self.shift) # TODO test, not sure if this works
            #     return newimg
        return super().transform_image(image, output_size=output_size, labels=labels, force_size=force_size)
    def invert(self):
        """Invert the transform.

        Note: This will return incorrect results for some non-affine transforms.
        Currently it just swaps the order of the points.

        """
        return self.__class__(points_start=self.points_end, points_end=self.points_start, **self.params)

# TODO improve optimisation with the jacobian
class PointTransformNoInverse(PointTransform):
    """For transforms which do not have an analytic inverse.

    Requires subclass to have {"invert": False} as a parameter.

    Automatically uses numerical routines to define the inverse.  To subclass,
    define the "_transform" function.  The function still needs to be
    invertable, i.e., it still needs to be a bijection.  For these, unlike
    normal, the _transform function must take three arguments: the points to
    transform, the starting points, and the ending points.

    We assume that the non-invertable transform is actually the inverse
    transform, since image transforms usually operate this way and they are more
    computationally expensive.  Passing the "invert=False" argument to the
    constructor will change this.

    """
    def __init__(self, *args, **kwargs):
        self._inv_transform_cache = {}
        super().__init__(*args, **kwargs)
    # Use the inverse transform by default
    def transform(self, points):
        points = np.asarray(points)
        is_1d = False
        if points.ndim == 1:
            is_1d = True
            points = points[None]
        assert points.shape[1] == 3, "Input points must be in volume space"
        if self.params["invert"]:
            print("Fast inverse transform of", points.shape)
            res = self._transform(points, points_start=self.points_start, points_end=self.points_end)
        else:
            print("Slow transform of", points.shape)
            if points.shape[0] > 1000:
                raise ValueError("Too many points to invert, this will take forever.")
            res = np.asarray([self._inv_transform_cache[tuple(p)] if tuple(p) in self._inv_transform_cache.keys() else invert_function_numerical(lambda x,self=self : self._transform(x, self.points_end, self.points_start), p) for p in points])
        return res[0] if is_1d else res
    def invert(self):
        return self.__class__(points_start=self.points_end, points_end=self.points_start, invert=(not self.params["invert"]))

class TranslateRotate(AffineTransform,PointTransform):
    NAME = "Translate and rotate"
    SHORTCUT_KEY = "T"
    SORT_WEIGHT = -99
    def _fit(self):
        demeaned_start = self.points_start - np.mean(self.points_start, axis=0)
        demeaned_end = self.points_end - np.mean(self.points_end, axis=0)
        U,S,V = np.linalg.svd(demeaned_start.T @ demeaned_end)
        self.matrix = U@V
        self.shift = np.mean(self.points_start @ self.matrix - self.points_end, axis=0)

class TranslateRotateRescaleByPlane(AffineTransform,PointTransform):
    """Translate, Rotate, and Rescale for planes (e.g., sections)

    We do not want to perform a linear regression from starting points to ending
    points as in TranslateRotateRescale, because this can cause some gnarly skew
    due to the difference in point spacing in the thin dimension compared to the
    thicker dimensions.  So, this finds a 2D plane (two high-variance
    dimensions) that maximises shared variance between the point clouds, and
    then performs two regressions: one for the two high variance dimensions, and
    another separately for the lowest-variance dimension.

    """
    NAME = "Translate, rotate, and rescale along a plane"
    SHORTCUT_KEY = "P"
    SORT_WEIGHT = -96
    DEFAULT_PARAMETERS = {"invert": False}
    def _fit(self):
        if self.params['invert']:
            _start = self.points_end
            _end = self.points_start
        else:
            _start = self.points_start
            _end = self.points_end
        # PCA
        demeaned_start = _start - np.mean(_start, axis=0)
        demeaned_end = _end - np.mean(_end, axis=0)
        U,S,V = np.linalg.svd(demeaned_start.T @ demeaned_end)
        assert np.all(np.sort(S)[::-1] == S), "SVD is not sorted correctly"
        # Regression for the high-variance dimensions
        proj_start = demeaned_start @ U[:,:2]
        proj_end = demeaned_end @ V.T[:,:2]
        _proj_start = np.hstack([np.ones((proj_start.shape[0],1)), proj_start])
        reg_coefs = np.linalg.inv(_proj_start.T @ _proj_start) @ _proj_start.T @ proj_end
        # Regression for the low-variance dimension
        depth_start = demeaned_start @ U[:,[2]]
        depth_end = demeaned_end @ V.T[:,[2]]
        _depth_start = np.hstack([np.ones((depth_start.shape[0],1)), depth_start])
        depth_reg_coefs = np.linalg.inv(_depth_start.T @ _depth_start) @ _depth_start.T @ depth_end
        # Combine the two
        self.matrix = U @ (scipy.linalg.block_diag(reg_coefs[1:], 0) + np.diag([0, 0, depth_reg_coefs[1,0]])) @ V
        if self.params['invert']:
            self.matrix = np.linalg.inv(self.matrix)
        self.shift = np.mean(self.points_start @ self.matrix - self.points_end, axis=0)
    def invert(self):
        return self.__class__(points_start=self.points_end, points_end=self.points_start, invert=(not self.params["invert"]))

class TranslateRotateRescale(AffineTransform,PointTransform):
    NAME = "Translate, rotate, and rescale"
    SHORTCUT_KEY = "R"
    SORT_WEIGHT = -97
    DEFAULT_PARAMETERS = {"invert": False}
    def _fit(self):
        if self.params['invert']:
            _start = self.points_end
            _end = self.points_start
        else:
            _start = self.points_start
            _end = self.points_end
        start = np.hstack([np.ones((_start.shape[0],1)), _start])
        reg_coefs = np.linalg.inv(start.T @ start) @ start.T @ _end
        self.matrix = reg_coefs[1:]
        if self.params['invert']:
            self.matrix = np.linalg.inv(self.matrix)
        self.shift = np.mean(self.points_start @ self.matrix - self.points_end, axis=0)
    def invert(self):
        return self.__class__(points_start=self.points_end, points_end=self.points_start, invert=(not self.params["invert"]))

class TranslateRotate2D(AffineTransform,PointTransform): # Deprecated
    NAME = "Translate and rotate in 2D only"
    def _fit(self):
        demeaned_start = self.points_start - np.mean(self.points_start, axis=0)
        demeaned_end = self.points_end - np.mean(self.points_end, axis=0)
        U,S,V = np.linalg.svd(demeaned_start[:,1:3].T @ demeaned_end[:,1:3])
        corner_matrix = U@V
        self.matrix = np.vstack([[[1, 0, 0]], np.hstack([[[0],[0]], corner_matrix])])
        self.shift = np.mean(self.points_start @ self.matrix - self.points_end, axis=0)

class Translate(AffineTransform,PointTransform):
    NAME = "Translate"
    SORT_WEIGHT = -100
    def _fit(self):
        self.matrix = np.eye(3)
        self.shift = np.mean(self.points_start - self.points_end, axis=0)

class Flip(AffineTransform,Transform): # Deprecated
    NAME = "Flip"
    DEFAULT_PARAMETERS = {"z": False, "y": False, "x": False, "zthickness": 0, "ythickness": 0, "xthickness": 0}
    def _fit(self):
        sign = lambda x : -1 if self.params[x] else 1
        self.matrix = np.asarray([[sign("z"), 0, 0], [0, sign("y"), 0], [0, 0, sign("x")]])
        self.shift = np.asarray([max(0, self.params[c+"thickness"]-1)*int(self.params[c]) for c in ["z", "y", "x"]])
    def invert(self):
        return self

class FlipFixed(AffineTransform,Transform):
    NAME = "Flip"
    DEFAULT_PARAMETERS = {"z": False, "y": False, "x": False, "zthickness": 0, "ythickness": 0, "xthickness": 0}
    def _fit(self):
        sign = lambda x : -1 if self.params[x] else 1
        self.matrix = np.asarray([[sign("z"), 0, 0], [0, sign("y"), 0], [0, 0, sign("x")]])
        self.shift = -np.asarray([self.params[c+"thickness"]*int(self.params[c]) for c in ["z", "y", "x"]])
    def invert(self):
        return self

class TranslateFixed(AffineTransform,Transform):
    NAME = "Translate"
    DEFAULT_PARAMETERS = {"z": 0.0, "y": 0.0, "x": 0.0}
    GUI_DRAG_PARAMETERS = ["z", "y", "x"]
    def _fit(self):
        self.matrix = np.eye(3)
        self.shift = np.asarray([-self.params["z"], -self.params["y"], -self.params["x"]])
    def invert(self):
        return self.__class__(x=-self.params["x"], y=-self.params["y"], z=-self.params["z"])

class TranslateRotateFixed(AffineTransform,Transform):
    NAME = "Translate and rotate"
    SHORTCUT_KEY = "t"
    SORT_WEIGHT = -99
    DEFAULT_PARAMETERS = {"z": 0.0, "y": 0.0, "x": 0.0, "zrotate": 0.0, "yrotate": 0.0, "xrotate": 0.0, "invert": False}
    GUI_DRAG_PARAMETERS = ["z", "y", "x"]
    def _fit(self):
        self.matrix = rotation_matrix(self.params["zrotate"], self.params["yrotate"], self.params["xrotate"])
        if self.params['invert']:
            self.matrix = self.matrix.T
        self.shift = np.asarray([-self.params["z"], -self.params["y"], -self.params["x"]])
    def invert(self):
        newzyx = [self.params["z"], self.params["y"], self.params["x"]] @ self.matrix.T
        return self.__class__(zrotate=self.params["zrotate"], yrotate=self.params["yrotate"], xrotate=self.params["xrotate"], z=-newzyx[0], y=-newzyx[1], x=-newzyx[2], invert=(not self.params['invert']))

class TranslateRotateRescaleFixed(AffineTransform,Transform):
    NAME = "Translate, rotate, and rescale"
    SHORTCUT_KEY = "r"
    SORT_WEIGHT = -98
    DEFAULT_PARAMETERS = {"z": 0.0, "y": 0.0, "x": 0.0, "zrotate": 0.0, "yrotate": 0.0, "xrotate": 0.0, "zscale": 1.0, "yscale": 1.0, "xscale": 1.0, "invert": False}
    GUI_DRAG_PARAMETERS = ["z", "y", "x"]
    def _fit(self):
        self.matrix = rotation_matrix(self.params["zrotate"], self.params["yrotate"], self.params["xrotate"]) @ np.asarray([[self.params["zscale"], 0, 0], [0, self.params["yscale"], 0], [0, 0, self.params["xscale"]]])
        if self.params['invert']:
            self.matrix = np.linalg.inv(self.matrix)
        self.shift = np.asarray([-self.params["z"], -self.params["y"], -self.params["x"]])
    def invert(self):
        newzyx = [self.params["z"], self.params["y"], self.params["x"]] @ np.linalg.inv(self.matrix)
        return self.__class__(zrotate=self.params["zrotate"], yrotate=self.params["yrotate"], xrotate=self.params["xrotate"], z=-newzyx[0], y=-newzyx[1], x=-newzyx[2], zscale=self.params["zscale"], yscale=self.params["yscale"], xscale=self.params["xscale"], invert=(not self.params['invert']))

class TranslateRotateRescale2DFixed(AffineTransform,Transform): # Deprecated
    DEFAULT_PARAMETERS = {"y": 0.0, "x": 0.0, "rotate": 0.0, "scale": 1.0}
    GUI_DRAG_PARAMETERS = [None, "y", "x"]
    def _fit(self):
        self.matrix = rotation_matrix(self.params["rotate"], 0, 0) @ np.asarray([[1, 0, 0], [0, self.params["scale"], 0], [0, 0, self.params["scale"]]])
        self.shift = np.asarray([0, -self.params["y"], -self.params["x"]])
    def invert(self):
        newzyx = [0, self.params["y"], self.params["x"]] @ self.matrix.T
        return self.__class__(rotate=-self.params["rotate"], y=-newzyx[1], x=-newzyx[2], scale=1/self.params["scale"])

class ShearFixed(AffineTransform,Transform):
    NAME = "Shear"
    DEFAULT_PARAMETERS = {"yzshear": 0, "xzshear": 0, "xyshear": 0}
    def _fit(self):
        self.shift = np.zeros(3)
        self.matrix = np.asarray([[1, 0, 0], [self.params["yzshear"], 1, 0], [self.params["xzshear"], self.params["xyshear"], 1]])
    def invert(self):
        return self.__class__(yzshear=-self.params["yzshear"], xzshear=self.params["xyshear"]*self.params["yzshear"]-self.params["xzshear"], xyshear=-self.params["xyshear"])

Shear = ShearFixed

class MatrixFixed(AffineTransform,Transform):
    """Directly use a transformation matrix.  Does not check to make sure the matrix is valid, use at your own risk!"""
    NAME = "Transformation matrix"
    DEFAULT_PARAMETERS = {"a11": 1, "a12": 0, "a13": 0, "a21": 0, "a22": 1, "a23": 0, "a31": 0, "a32": 0, "a33": 1, "x": 0, "y": 0, "z": 0}
    GUI_DRAG_PARAMETERS = ["z", "y", "x"]
    def _fit(self):
        p = lambda num : self.params[f"a{num}"]
        self.matrix = np.asarray([[p(11), p(12), p(13)], [p(21), p(22), p(23)], [p(31), p(32), p(33)]])
        self.shift = np.asarray([-self.params["z"], -self.params["y"], -self.params["x"]])
    def invert(self):
        p = lambda num : self.params[f"a{num}"]
        newzyx = [self.params["z"], self.params["y"], self.params["x"]] @ self.matrix.T
        return self.__class__(a11=p(11), a12=p(21), a13=p(31), a21=p(12), a22=p(22), a23=p(32), a31=p(13), a32=p(23), a33=p(33), z=-newzyx[0], y=-newzyx[1], x=-newzyx[2])

class Identity(AffineTransform,Transform):
    NAME = "No transform"
    def _fit(self):
        self.matrix = np.eye(3)
        self.shift = np.zeros(3)
    def _transform(self, points):
        return points
    def invert(self):
        return self.__class__()
    def transform_image(self, image, output_size=None, labels=None, force_size=None):
        """More efficient implementation of image transformation"""
        # TODO This doesn't work for different output_size values
        return image

class Rescale(AffineTransform,Transform):
    NAME = "Rescale"
    DEFAULT_PARAMETERS = {"z": 1.0, "y": 1.0, "x": 1.0}
    def _fit(self):
        self.matrix = np.diag([self.params["z"], self.params["y"], self.params["x"]])
        self.shift = np.asarray([0, 0, 0])
    def invert(self):
        return self.__class__(z=1/self.params["z"], y=1/self.params["y"], x=1/self.params["x"])

class Triangulation(PointTransform):
    """Using a mesh/triangulation to deform the volume.

    This uses a Delaunay triangulation for the inverse transform.  Because scipy
    does not support using an arbitrary triangulation here, we manually iterate
    through to determine containment of a point in each simplex instead of using
    the built-in scipy function.  Then, we apply the relevant linear transform
    to each.
    """
    NAME = "Nonlinear 3D triangulation"
    SHORTCUT_KEY = "V"
    SORT_WEIGHT = 100
    DEFAULT_PARAMETERS = {"invert": True} # Start with inverted because inverted is slower for points and faster for images
    def _fit(self):
        # To avoid out of bounds, we add a few pseudo points.  We do this by
        # finding the convex hull, centering it, and scaling it, and then
        # shifting the scaled points back from the centering.  To avoid sharp
        # angles for near-coplannar point clouds, we shift the points in all
        # dimensions by a small value first.  We assign these points a simple
        # linear transformed version of the points they are derived from.
        SCALE_FACTOR = 1000
        if self.params["invert"]:
            before = self.points_end
            after = self.points_start
        else:
            before = self.points_start
            after = self.points_end
        _rns = np.random.RandomState(0).randn(*before.shape)*.0001 # Break symmetry
        before = before + _rns
        t = scipy.spatial.Delaunay(before) # Triangulation
        assert np.all(t.points == before), "Coplannar points"
        hull_points_inds = np.unique(t.convex_hull.flatten())
        hull_points_vecs = after[hull_points_inds] - before[hull_points_inds]
        hull_mean_shift = np.mean(before[hull_points_inds], axis=0)
        if self.params["invert"]:
            self.pseudopoints_end = SCALE_FACTOR*(before[hull_points_inds] - hull_mean_shift) + hull_mean_shift
            #self.pseudopoints_end += 5*SCALE_FACTOR*np.sign(self.pseudopoints_end-hull_mean_shift)
            self.pseudopoints_start = self.pseudopoints_end + hull_points_vecs
        else:
            self.pseudopoints_start = SCALE_FACTOR*(before[hull_points_inds] - hull_mean_shift) + hull_mean_shift
            #self.pseudopoints_start += 5*SCALE_FACTOR*np.sign(self.pseudopoints_start-hull_mean_shift)
            self.pseudopoints_end = self.pseudopoints_start + hull_points_vecs
        self.all_points_start = np.concatenate([self.points_start, self.pseudopoints_start])
        self.all_points_end = np.concatenate([self.points_end, self.pseudopoints_end])
    def _transform(self, points):
        points = np.asarray(points)
        start = self.all_points_start
        end = self.all_points_end
        tri_points = self.all_points_start if not self.params["invert"] else self.all_points_end
        _rns = np.random.RandomState(0).randn(*tri_points.shape)*.0001 # Break symmetry
        delaunay = scipy.spatial.Delaunay(tri_points+_rns)
        assert np.max(delaunay.points-tri_points)<.1, "Wrong order of Delaunay triangulation, are some points coplannar?"
        if self.params['invert']:
            newpoints = np.zeros_like(points)*np.nan
            for simp in delaunay.simplices:
                insimp = scipy.spatial.Delaunay(start[simp]).find_simplex(points)>=0
                if np.sum(insimp) == 0: continue
                coefs_rhs = np.concatenate([start[simp], np.ones(len(simp))[:,None]], axis=1)
                coefs_lhs = end[simp]
                params = np.linalg.inv(coefs_rhs) @ coefs_lhs
                newpoints[insimp] = np.concatenate([points[insimp], np.ones(sum(insimp))[:,None]], axis=1) @ params
            assert not np.any(np.isnan(newpoints)), "Point was outside of simplex or invalid input points"
            return newpoints
        else: # For the non-inverted case, we can use the original triangulation and improve performance
            insimp = delaunay.find_simplex(points)
            assert np.all(insimp>=0), "Points outside domain, increase scale factor in code"
            newpoints = np.zeros_like(points)*np.nan
            for i,simp in enumerate(delaunay.simplices):
                if np.sum(insimp==i) == 0: continue
                coefs_rhs = np.concatenate([start[simp], np.ones(len(simp))[:,None]], axis=1)
                coefs_lhs = end[simp]
                params = np.linalg.inv(coefs_rhs) @ coefs_lhs
                newpoints[insimp==i] = np.concatenate([points[insimp==i], np.ones(sum(insimp==i))[:,None]], axis=1) @ params
            assert not np.any(np.isnan(newpoints)), "Not sure why this should ever happen?"
            return newpoints
    def invert(self):
        return self.__class__(invert=(not self.params["invert"]), points_start=self.points_end, points_end=self.points_start)

class Triangulation2D(PointTransform):
    """Using a mesh/triangulation to deform the volume in two dimensions.

    This is the recommended nonlinear transform for any image that looks like a
    pancake (flat but not extremely thin).

    If the components of the normal vector are all zero, the normal vector will
    be detected automatically.  

    This uses a Delaunay triangulation for the inverse transform.  Because scipy
    does not support using an arbitrary triangulation here, we manually iterate
    through to determine containment of a point in each simplex instead of using
    the built-in scipy function.  Then, we apply the relevant linear transform
    to each.

    """
    NAME = "Nonlinear projected triangulation"
    SHORTCUT_KEY = "N"
    SORT_WEIGHT = 99
    DEFAULT_PARAMETERS = {"invert": True, "normal_z": 0.0, "normal_y": 0.0, "normal_x": 0.0} # Start with inverted because inverted is slower for points and faster for images
    def _fit(self):
        # To avoid out of bounds, we add a few pseudo points.  We do this by
        # finding the convex hull, centering it, and scaling it, and then
        # shifting the scaled points back from the centering.  To avoid sharp
        # angles for near-coplannar point clouds, we shift the points in all
        # dimensions by a small value first.  We assign these points a simple
        # linear transformed version of the points they are derived from.
        SCALE_FACTOR = 100
        if self.params["invert"]:
            before = self.points_end
            after = self.points_start
        else:
            before = self.points_start
            after = self.points_end
        # Automatically find the normal if it wasn't manually specified
        if self.params['normal_z'] == 0 and self.params['normal_y'] == 0 and self.params['normal_x'] == 0:
            demeaned_before = before - np.mean(before, axis=0)
            U,S,V = np.linalg.svd(demeaned_before.T @ demeaned_before)
            assert np.all(np.sort(S)[::-1] == S), "SVD is not sorted correctly"
            self.normal = U[:,2]
        else:
            self.normal = np.asarray([self.params["normal_z"], self.params["normal_y"], self.params["normal_x"]])
            self.normal /= np.sqrt(np.sum(np.square(self.normal)))
        # Find two vectors to form the basis for the plane.  Suffix "B" to indicate we are in this basis
        vec1 = np.asarray([1., 0, 0]) if np.asarray([1., 0, 0]) @ self.normal < .99 else np.asarray([0, 1., 0]) # Can be any vector in a different direction than the normal, these are a bit easier to interpret
        vec1 -= (vec1 @ self.normal) * self.normal
        vec1 /= np.sqrt(np.sum(np.square(vec1)))
        self.B = np.asarray([vec1, np.cross(self.normal, vec1)]).T
        beforeB = before @ self.B
        t = scipy.spatial.Delaunay(beforeB) # Triangulation
        assert np.all(t.points == beforeB), "Coplannar points"
        hull_points_inds = np.unique(t.convex_hull.flatten())
        hull_points_vecs = after[hull_points_inds] - before[hull_points_inds]
        hull_mean_shift = np.mean(before[hull_points_inds], axis=0)
        if self.params["invert"]:
            self.pseudopoints_end = SCALE_FACTOR*(before[hull_points_inds] - hull_mean_shift) + hull_mean_shift
            #self.pseudopoints_end += 5*SCALE_FACTOR*np.sign(self.pseudopoints_end-hull_mean_shift)
            self.pseudopoints_start = self.pseudopoints_end + hull_points_vecs
        else:
            self.pseudopoints_start = SCALE_FACTOR*(before[hull_points_inds] - hull_mean_shift) + hull_mean_shift
            #self.pseudopoints_start += 5*SCALE_FACTOR*np.sign(self.pseudopoints_start-hull_mean_shift)
            self.pseudopoints_end = self.pseudopoints_start + hull_points_vecs
        self.all_points_start = np.concatenate([self.points_start, self.pseudopoints_start])
        self.all_points_end = np.concatenate([self.points_end, self.pseudopoints_end])
    def _transform(self, points):
        # Project all points into the basis defined in _fit.  This is indicated
        # by "B" suffix.  Then perform the triangulation in that 2-dimensional
        # space, and then compute the new points in 3D by holding the
        # interpolation constant in the direction normal to the space.
        points = np.asarray(points)
        pointsB = points @ self.B
        start = self.all_points_start
        startB = start @ self.B
        end = self.all_points_end
        tri_pointsB = (self.all_points_start if not self.params["invert"] else self.all_points_end) @ self.B
        delaunay = scipy.spatial.Delaunay(tri_pointsB)
        assert np.all(delaunay.points == tri_pointsB), "Coplannar points"
        if self.params['invert']:
            newpoints = np.zeros_like(points)*np.nan
            if points.shape[0] > 1000:
                print("Warning, using slow transform to transform many points, try inverting")
            for simp in delaunay.simplices:
                insimp = scipy.spatial.Delaunay(startB[simp]).find_simplex(pointsB)>=0
                if np.sum(insimp) == 0: continue
                _start = np.concatenate([start[simp], start[[simp[0]]]+self.normal], axis=0)
                _end = np.concatenate([end[simp], end[[simp[0]]]+self.normal], axis=0)
                coefs_rhs = np.concatenate([_start, np.ones(len(simp)+1)[:,None]], axis=1)
                coefs_lhs = _end
                params = np.linalg.inv(coefs_rhs) @ coefs_lhs
                newpoints[insimp] = np.concatenate([points[insimp], np.ones(np.sum(insimp))[:,None]], axis=1) @ params
            assert not np.any(np.isnan(newpoints)), "Point was outside of simplex or invalid input points"
            return newpoints
        else: # For the non-inverted case, we can use the original triangulation and improve performance
            insimp = delaunay.find_simplex(pointsB)
            assert np.all(insimp>=0), "Points outside domain, increase scale factor in code"
            newpoints = np.zeros_like(points)*np.nan
            for i,simp in enumerate(delaunay.simplices):
                if np.sum(insimp==i) == 0: continue
                # Perform linear regression to get a map from the start to the
                # end.  Add an extra point with the normal added so we get a
                # 3D-to-3D map.
                _start = np.concatenate([start[simp], start[[simp[0]]]+self.normal], axis=0)
                _end = np.concatenate([end[simp], end[[simp[0]]]+self.normal], axis=0)
                coefs_rhs = np.concatenate([_start, np.ones(len(simp)+1)[:,None]], axis=1)
                coefs_lhs = _end
                params = np.linalg.inv(coefs_rhs) @ coefs_lhs
                newpoints[insimp==i] = np.concatenate([points[insimp==i], np.ones(np.sum(insimp==i))[:,None]], axis=1) @ params
            assert not np.any(np.isnan(newpoints)), "Not sure why this should ever happen?"
            return newpoints
    def invert(self):
        return self.__class__(invert=(not self.params["invert"]), points_start=self.points_end, points_end=self.points_start, normal_z=self.params["normal_z"], normal_y=self.params["normal_y"], normal_x=self.params["normal_x"])


# This doesn't work very well
class DistanceWeightedAverageGaussian(PointTransformNoInverse): # Deprecated
    DEFAULT_PARAMETERS = {"extent": 1, "invert": False}
    def _transform(self, points, points_start, points_end):
        points = np.asarray(points, dtype="float")
        baseline = np.zeros_like(points[:,0])
        pos = np.zeros_like(points)
        for i in range(0, len(points_start)):
            mvn = scipy.stats.multivariate_normal(points_start[i], np.eye(3)*self.params["extent"])
            baseline += mvn.pdf(points)
            for j in range(0, 3):
                pos[:,j] += mvn.pdf(points)*(points_end[i][j]-points_start[i][j])
        epsilon = 1e-100 # For numerical stability
        pos += np.mean(points_end-points_start, axis=0, keepdims=True)*epsilon
        pos /= (baseline[:,None] + epsilon)
        return points + pos

# import numba
# class DistanceWeightedAverage(PointTransformNoInverse):
#     """Implements a weighted average according to inverse sequare distance.

#     The code here is highly optimised for speed, and is really hard to decipher.
#     The equation is:

#         \\sum_i v_i/w_i + \\epsilon \\bar{v}
#         -----------------------------------
#                      w_i

#     where w_i = 1/(d_i^2 + \\epsilon), d is the distance of the test point to the
#     point i, and v_i is the end minus the start for point pair i, where \\bar{v}
#     is the mean across all points.

#     I think it might be a bug to have the epsilon multiplied by \\bar{v} (this
#     makes it essentially always zero), and instead I actually want the same term
#     in the denominator as well, but it works so who cares.

#     """
#     NAME = "Nonlinear distance weighted average"
#     DEFAULT_PARAMETERS = {"invert": False}
#     @staticmethod
#     @numba.jit(nopython=True, parallel=True)
#     def _loop(points, points_start, points_end, epsilon):
#         baseline = np.zeros_like(points[:,0])
#         pos = np.zeros_like(points)
#         sumsquare = np.sum(np.square(points), axis=1)
#         for i in range(0, len(points_start)):
#             dist = 1/(sumsquare - 2*points[:,0]*points_start[i][0] - 2*points[:,1]*points_start[i][1] - 2*points[:,2]*points_start[i][2] + (np.sum(np.square(points_start[i]))+epsilon))
#             baseline += dist
#             for j in range(0, 3):
#                 pos[:,j] += dist*(points_end[i][j]-points_start[i][j])
#         return pos,baseline
#     def _transform(self, points, points_start, points_end):
#         if points.shape[0] > 20:
#             print("Array transform")
#             return self._transform_array(points, points_start, points_end)
#         #_t = time.time()
#         points = np.asarray(points, dtype="float")
#         baseline = np.zeros_like(points[:,0])
#         pos = np.zeros_like(points)
#         epsilon = 1e-200 # For numerical stability
#         sumsquare = np.sum(np.square(points), axis=1)
#         for i in range(0, len(points_start)):
#             dist = 1/(sumsquare - 2*points[:,0]*points_start[i][0] - 2*points[:,1]*points_start[i][1] - 2*points[:,2]*points_start[i][2] + (np.sum(np.square(points_start[i]))+epsilon))
#             baseline += dist
#             for j in range(0, 3):
#                 pos[:,j] += dist*(points_end[i][j]-points_start[i][j])
#         pos += np.mean(points_end-points_start, axis=0, keepdims=True)*epsilon
#         pos /= baseline[:,None]
#         #print("Time:", time.time()-_t)
#         return points + pos
#     def _transform_array(self, points, points_start, points_end):
#         #_t = time.time()
#         points = np.asarray(points, dtype="float", order="F")
#         epsilon = 1e-200 # For numerical stability
#         pos,baseline = self._loop(points, points_start, points_end, epsilon)
#         pos += np.mean(points_end-points_start, axis=0, keepdims=True)*epsilon
#         pos /= baseline[:,None]
#         return points + pos

def compose_transforms(a, b):
    # Skip for the identity transform
    if isinstance(a, Identity):
        return b
    if isinstance(b, Identity):
        return a
    # Special cases for linear and for adding to a class (not yet fitted)
    if isinstance(a, Transform) and isinstance(b, Transform):
        if isinstance(b, PointTransform):
            return compose_transforms(a, b.__class__)(points_start=b.points_start, points_end=b.points_end, **b.params)
        else:
            return compose_transforms(a, b.__class__)(**b.params)
    # if isinstance(a, Transform) and isinstance(b, Transform):
    #     return Composed(a, b)
    if isinstance(a, Transform) and not isinstance(b, Transform):
        inherit = PointTransform if issubclass(b, PointTransform) else Transform
        if isinstance(a, AffineTransform) and issubclass(b, AffineTransform):
            class ComposedPartialAffine(AffineTransform,inherit):
                DEFAULT_PARAMETERS = b.DEFAULT_PARAMETERS # b.params # Changed from b.DEFAULT_PARAMETERS
                GUI_DRAG_PARAMETERS = b.GUI_DRAG_PARAMETERS
                def __new__(cls, *args, **kwargs): # Strip identity if necessary
                    if b is Identity:
                        return a
                    return super(ComposedPartialAffine, cls).__new__(cls)
                def __init__(self, points_start=None, points_end=None, *args, **kwargs):
                    extra_args = {}
                    if points_start is not None and points_end is not None:
                        extra_args['points_start'] = points_start
                        extra_args['points_end'] = points_end
                    self.b_type = b
                    self.b = b(*args, **kwargs, **extra_args)
                    super().__init__(*args, **kwargs, **extra_args)
                    if self.b_type is Identity:
                        self = self.a
                def _fit(self):
                    self.matrix = a.matrix @ self.b.matrix
                    self.shift = a.shift @ self.b.matrix + self.b.shift
                def __repr__(self):
                    return repr(a) + " + " + repr(self.b)
                @staticmethod
                def pretransform(*args, **kwargs):
                    return a
                def invert(self):
                    return self.b.invert() + a.invert()
            return ComposedPartialAffine
        else:
            class ComposedPartial(inherit):
                DEFAULT_PARAMETERS = b.DEFAULT_PARAMETERS #  b.params # Changed from b.DEFAULT_PARAMETERS
                GUI_DRAG_PARAMETERS = b.GUI_DRAG_PARAMETERS
                def __new__(cls, *args, **kwargs): # Strip identity if necessary
                    if b is Identity:
                        return a
                    return super(ComposedPartial, cls).__new__(cls)
                def __init__(self, points_start=None, points_end=None, *args, **kwargs):
                    extra_args = {}
                    if points_start is not None and points_end is not None:
                        extra_args['points_start'] = points_start
                        extra_args['points_end'] = points_end
                    self.b_type = b
                    self.b = b(*args, **kwargs, **extra_args)
                    super().__init__(**extra_args, **self.b.params)
                def _transform(self, points):
                    return self.b.transform(a.transform(points))
                def inverse_transform(self, points):
                    return a.inverse_transform(self.b.inverse_transform(points))
                def invert(self):
                    raise NotImplementedError
                def __repr__(self):
                    return repr(a) + " + " + repr(self.b)
                def invert(self):
                    return self.b.invert() + a.invert()
                @staticmethod
                def pretransform(*args, **kwargs):
                    return a
            return ComposedPartial
    raise NotImplementedError("Invalid composition")


