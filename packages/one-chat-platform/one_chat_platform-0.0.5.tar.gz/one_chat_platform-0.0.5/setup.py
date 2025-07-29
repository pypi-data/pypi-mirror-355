from setuptools import setup, find_packages

# อ่าน long description จาก README.md (ถ้ามี)
# try:
#     with open("README.md", "r", encoding="utf-8") as fh:
#         long_description = fh.read()
# except FileNotFoundError:
#     long_description = ""

setup(
    name="one-chat-platform",  # ชื่อ package
    version="0.0.5",  # เวอร์ชันของ package
    description="",
    # long_description=long_description,  # รายละเอียดยาว
    # long_description_content_type="text/markdown",  # ประเภทของเนื้อหาคำอธิบายยาว
    author="Pargorn Ruasijan (xNewz)",  # ชื่อของผู้พัฒนา
    author_email="pargorn.ru@gmail.com",  # อีเมลของผู้พัฒนา
    packages=find_packages(),  # หาชื่อ package ที่อยู่ในโฟลเดอร์
    install_requires=[
        "requests",  # ไลบรารีที่จำเป็น
        "urllib3"
    ],
    python_requires=">=3.6",  # ระบุเวอร์ชันของ Python ที่รองรับ
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
