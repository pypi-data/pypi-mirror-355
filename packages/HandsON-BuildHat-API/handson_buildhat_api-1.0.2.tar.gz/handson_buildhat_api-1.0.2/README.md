HandsON Build Hat API
=======
**Production** : HandsON Technology co., ltd.  
**Author** : HaNeul Jung (caffeine.reload@gmail.com)  
**Last Update** : 2025-06-07

## 개요
제작된 빌드햇의 제어에 필요한 API 라이브러리

## 구동 환경
### 컨트롤러
|이름|설명|
|:--|:--|
|Raspberry PI 4, 5|정상 동작 확인|
|Jetson Orin Nano, Nano|정상 동작 확인 (하드웨어 구조가 라즈베리파이 버전과 다름)|

### 종속성
 - python3-serial

## 예제
모든 API는 기존 Spike Legacy와 문법적으로 동일  

```python
from HandsON_BuildHat_API import ColorSensor, Motor

motor = Motor('A')
colorsensor = ColorSensor('B')

reflected = colorsensor.get_reflected_light()
motor.start(100)
```

자세한 문법은 Lego Spike Legacy 앱에서 확인