# J123 캡스톤 디자인

# 깃허브 최상위 폴더
- app.py: Flask 실행파일
- assets: README.md에 사용될 이미지 등을 저장
- static: 자바스크립트 등 정적 웹페이지 구성요소 저장
- templates: index.html 등 웹 페이지 저장

# 깃허브 브랜치 설명
- main: 문서화 및 전체 코드 업로드
- deploy: README.md, assets 같은 폴더를 제외하고 실제 클라우드에 올릴 코드만 업로드

# 프로젝트 구조
## 플로우 차트
![flowchart](./assets/flowchart.jpeg)
## 시퀀스 다이어그램
![SequenceDiagram](./assets/SequenceDiagram.jpg)
# 웹페이지 설명

## Flask 페이지
Flask 페이지는 서버에서 localhost로만 실행되며, GPS 정보를 화면에 표시

### /
홈페이지<br/>
드론 조작 및 로깅 정보 확인 가능

### /logging
로깅 페이지<br/>
임시 페이지이며, 로깅 정보만 확인 가능

### /register
등록 페이지<br/>
태그 등록/삭제, 로깅 지원

# MongoDB
```MongoDB
[
  {
    _id: ObjectId('68024808fb70db1095d861e2'),
    name: 'Drone A',
    status: '활동 중',
    loaction: { lat: 37.7749, lon: -122.4194 },
    tag: {
      mac_address: 'AA:BB:CC:DD:EE:FF',
      tag_name: 'Tag-1',
      location: 'Zone A'
    }
  }
]
```

## 데이터 전송 방법
### flask
```python
@app.route('/submit/', methods=['POST'])
def submit():
    data = request.get_json()
    value = data.get('value')
    return f"Received value: {value}", 200
```