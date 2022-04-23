# FlaskFileServer
사용자 관리와 프로그램을 배포하기 위한 간단한 서버

# 설치

## 공통
먼저 비밀키를 생성합니다  
cmd 또는 bash를 열고 다음을 입력합니다  
```
python -c "import secrets; print(secrets.token_hex())" 
```

다음과 같은 출력을 볼 수 있습니다  
```
(venv) user_repos\FlaskFileServer>python -c "import secrets; print(secrets.token_hex())" 
50803eb5f7ad8be976c2c15488c2bac99cf9426c96968fc911ead851ae8773a7
```

출력된 키를 복사한 합니다  
FlaskFileServer\production.py을 열고 SECRET_KEY에 붙여넣기 합니다  
```
from config.default import *

SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'FileServer.db'))
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "50803eb5f7ad8be976c2c15488c2bac99cf9426c96968fc911ead851ae8773a7"
```


## 윈도우  
```
#가상환경 생성 후 진입
python -m venv venv
venv\Scripts\activate

#종속성 설치
python -m pip install -r requirements.txt

```

## 리눅스  
```
#가상환경 생성 후 진입
python -m venv venv
venv\bin\activate

#종속성 설치
python -m pip install -r requirements.txt

```


# 실행

## 윈도우
```
#가상환경 진입
venv\Scripts\activate

#스크립트 실행
run_production.cmd
```
