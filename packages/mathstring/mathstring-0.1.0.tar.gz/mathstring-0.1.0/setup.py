from setuptools import setup, find_packages

setup(
    name="mathstring",
    version="0.1.0",
    description="English:\nMathstring is a Python library designed to evaluate mathematical expressions provided as text strings. It supports basic arithmetic operations like addition, subtraction, multiplication, division, and modulus. The library is easy to use and integrates seamlessly into Python projects, allowing developers to quickly calculate results from textual equations.العربية:\nمكتبة Mathstring هي مكتبة بايثون تهدف إلى تقييم التعبيرات الرياضية المكتوبة كسلاسل نصية. تدعم العمليات الحسابية الأساسية مثل الجمع والطرح والضرب والقسمة وباقي القسمة. المكتبة سهلة الاستخدام وتندمج بسلاسة ضمن مشاريع بايثون، مما يتيح للمطورين حساب النتائج بسرعة من المعادلات النصية.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Ryan Alsaidani",
    author_email="ryan.alsaidani@gmail.com",
    url="https://github.com/ryan-alsaidani/mathstring",
    packages=find_packages(),
    python_requires='>=3.7',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Utilities",
        "Topic :: Education",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Natural Language :: Arabic",
        "Operating System :: OS Independent"
    ],
    keywords="calculator math equations text processing python",
    license="Custom License - All Rights Reserved",
    include_package_data=True,
    install_requires=[],
)
