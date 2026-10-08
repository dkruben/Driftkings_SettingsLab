package driftkings.utils {
    import flash.geom.Matrix;

    public class ScreenTransform {
        // Cancel the native page's translation/UI scale while keeping physical
        // screen pixels aligned with the stage (including marker hit testing).
        public static function pixelsToParent(parentGlobal:Matrix, scaleX:Number, scaleY:Number):Matrix {
            var inverse:Matrix = parentGlobal.clone();
            inverse.invert();
            var result:Matrix = new Matrix(scaleX, 0, 0, scaleY);
            result.concat(inverse);
            return result;
        }
    }
}
