# LambdaCalcEvaluator
**Current features:**
- Lambda abstractions: `λx.(body)`
- Assignments: `(expr) -> identifier`
- Beta-reduction
- Support for Church numerals: `0 = λf.λx.x, 1 = λf.λx.f x, etc.`
- Conversion between Church numerals and integers


**Missing features:**
- Alpha conversion
- Eta reduction
- Free/Bound variable analysis
- Lambdas with multiple parameters (this can be bypassed with currying)


**Commands:**
- `/bools`: Generate the abstractions for `TRUE` and `FALSE`.
