# mathstring

A Python library to calculate mathematical equations provided as text input.  
مكتبة بايثون لحساب المعادلات الرياضية المكتوبة كنص.

---

## Features | الميزات
- Calculate mathematical expressions given as strings.  
  حساب المعادلات الرياضية المقدمة كسلاسل نصية.
- Supports basic arithmetic operations: addition, subtraction, multiplication, division, modulus.  
  تدعم العمليات الحسابية الأساسية: جمع، طرح، ضرب، قسمة، باقي القسمة.
- Easy to use and integrate in your Python projects.  
  سهلة الاستخدام والدمج ضمن مشاريع بايثون.

---

## Limitations | العيوب
- Does not yet support variables or parentheses in expressions.  
- May produce errors with negative number multiplications like `2*-1`.  
- Workarounds using helper functions are available for complex expressions.

- لا تدعم المتغيرات الرياضية والأقواس بعد.  
- قد تظهر أخطاء في العمليات التي تتضمن ضرب عدد سالب مثل `2*-1`.  
- يمكن استخدام دوال داخلية لحساب تعبيرات معقدة كبديل.

---

## Note | ملاحظة

The library currently does **not support variables** in expressions.  
To use variables, preprocess the input string by replacing variables with their numeric values as strings before passing it to the calculator.

Negative numbers in expressions like `2*-1` may cause errors.  
Instead of writing `f'2*-1'`, use the helper function like: `f'2*{xxx("-1")}'`.

Parentheses are **not supported**, so you can simulate nested calculations by evaluating inner expressions first, for example:  
`f'1+1*{xxx("2*3")}+2'`.

This library works by calculating expressions from text, so you can implement your own preprocessing step to replace variables or complex parts with their evaluated numeric results before passing to the library.

المكتبة حالياً لا تدعم المتغيرات في التعبيرات.  
لاستخدام المتغيرات، يمكنك معالجة النص أولاً باستبدال المتغيرات بقيمها الرقمية على شكل نصوص قبل تمريرها للمكتبة.

الأعداد السالبة في تعبيرات مثل `2*-1` قد تسبب أخطاء.  
بدلاً من كتابة `f'2*-1'` استخدم دالة المساعدة مثل: `f'2*{xxx("-1")}'`.

الأقواس غير مدعومة، لذلك يمكنك محاكاة الحسابات المتداخلة بحساب التعبيرات الداخلية أولاً، مثلاً:  
`f'1+1*{xxx("2*3")}+2'`.

تعمل المكتبة بحساب التعبيرات النصية، لذلك يمكنك تطبيق معالجة أولية خاصة بك لاستبدال المتغيرات أو الأجزاء المعقدة بنتائجها الرقمية قبل تمريرها للمكتبة.

---

## Installation | التثبيت

You can install mathstring via pip:

```bash
pip install mathstring
```
```python
from mathstring import xxx

equation = "3+5*2-4/2"
result = xxx(equation)
print(f"Result: {result}")  # Output: 10.0

print(850*2000-300*400/70 == xxx("850*2000-300*400/70"))  # Output: True

# Example with nested calculation to simulate parentheses:
print(xxx(f'1+1*{xxx("2*3")}+2'))  # Output: 9

# Example using the helper function for negative numbers:
print(xxx(f'2*{xxx("-1")}'))  # Output: -2

```
## License | الرخصة

This project is licensed under a Custom License - All Rights Reserved.  
This software is the exclusive property of Ryan Al-saidani.  
No part of this software may be copied, modified, distributed, sold, sublicensed, or otherwise used  
in any form or by any means without prior written permission from the copyright holder.

هذا المشروع مرخص بموجب رخصة خاصة تحتفظ بكل الحقوق.  
لا يُسمح بنسخ أو تعديل أو توزيع أو بيع البرنامج بأي شكل أو وسيلة دون إذن كتابي مسبق من المؤلف.

---
## Author | المؤلف

**First name and last name:** Ryan Alsaidani  
**Email:** ryan.alsaidani@gmail.com  
**GitHub:** [https://github.com/ryan-alsaidani/mathstring](https://github.com/ryan-alsaidani/mathstring)

---