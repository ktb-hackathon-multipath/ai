## Docker 실행 가이드

### 개발 환경 실행 (Dockerfile.dev)

개발 환경을 위해 `Dockerfile.dev`을 사용합니다. 아래 명령어로 이미지를 빌드하고 컨테이너를 실행할 수 있습니다.
Dokcerfile의 상대경로에 따라 적절히 수정해서 사용할 수 있습니다. 현재 repository에 위치해있다면 그대로 쓰는 코드를 example로 올렸습니다.

```bash
docker build -f Dockerfile.dev -t mp-dev .
docker run -it --name mp-dev mp-dev /bin/bash
```

```bash
# 재접속
docker start mp-dev
docker exec -it mp-dev /bin/bash
```

```bash
docker build -f Dockerfile.prod -t mp-prod .
docker run -d -p 80:80 mp-prod
```

