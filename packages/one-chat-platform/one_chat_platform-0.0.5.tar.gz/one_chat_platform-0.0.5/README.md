## อัปเดตเวอร์ชันในไฟล์ setup.py

### เปิดไฟล์ setup.py และอัปเดตตัวแปร version เป็นเวอร์ชันใหม่

```python
setup(
    name='your_package',
    version='1.1.0',  # อัปเดตเวอร์ชันที่นี่
    ...
)
```

## สร้างแพ็กเกจใหม่

### ใช้คำสั่งเพื่อสร้างไฟล์สำหรับอัปโหลด

```bash
python setup.py sdist bdist_wheel
```

## อัปโหลดไปยัง PyPI

### ใช้ twine เพื่ออัปโหลดแพ็กเกจ

```bash
twine upload dist/*
```

## วิธีใช้

### แบบที่ 1

```python
from one_chat_platform import *

token = "Your Access Token"
to = "User ID or Group ID"
init(
    token,
    to,
)


def main():
    send_message(
        message="Test Successfull ✅",
    )


if __name__ == "__main__":
    main()
```

### แบบที่ 2

```python
from one_chat_platform import *

def main():
    send_message(
        token="Your Access Token",
        to="User ID or Group ID",
        message="Test Successfull ✅",
    )

if __name__ == "__main__":
    main()
```
