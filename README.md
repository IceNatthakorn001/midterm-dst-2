# Study Notes — สรุปบทเรียน ปี 2

เว็บสรุปบทเรียน + แบบทดสอบ 5 วิชา: ITDS231 Computer Networks, ITDS261 Software Engineering, ITDS211 Computer Architecture & OS, ITDS212 Computer System Lab, ITDS241 Web Technologies

- เว็บจริงอยู่ในโฟลเดอร์ `docs/` (GitHub Pages)
- เพิ่ม/แก้บทเรียน: แก้ไฟล์ใน `sum by claude` ของแต่ละวิชา แล้วรัน `python build.py` จากนั้น commit + push
- ลำดับบทกำหนดใน `SUBJECTS[...]["order"]` ของ `build.py` (บทใหม่ต้องเพิ่มชื่อโฟลเดอร์ในลิสต์นี้)
- quiz แบบเก่าได้ `assets/quiz.css`; quiz-pro (มี `<main id="qp-app">`) ได้แค่แถบนำทาง + `assets/quizpro.css`
- หน้า `review.html` = ทบทวนที่ถึงรอบ รวมทุก quiz-pro (อ่าน localStorage `sn-srs:<id>`; รายชื่อชุดสร้างอัตโนมัติใน `assets/srs-catalog.js`, โค้ดอยู่ใน `assets/srs.js`)

ต้องใช้: `pip install markdown-it-py mdit-py-plugins pillow`
