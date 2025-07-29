## CI 镜像打包

在 Actions 标签页选择 "Build and Push Docker Images (Manual Trigger)" 点 "Run workflow" 即可。

## 本地镜像打包

物理机上准备环境：

```bash
python tools/setupComfyUI.py --config comfyui_setup.json # 下载 ComfyUI 及插件
python tools/generateRequirements.py --config comfyui_setup.json # 生成总的依赖文件
```

打包：

```bash
bash build.sh
```

## 启动命令

**本地测试**

```bash
IMG=hub.6scloud.com/supertester/bizydraft-backend-comfyui:v202506062349
docker run -it --rm --network host \
 $IMG \
 bash -c "pip install --upgrade bizyui bizyengine && python3 /app/ComfyUI/main.py --cpu --listen 0.0.0.0 --disable-metadata --port 8188"
```

**comfyagent backend 启动**

```bash
IMG=hub.6scloud.com/supertester/bizydraft-backend-comfyui:v202506062349
docker run --rm --network host \
 -e BIZYAIR_SERVER_MODE=True \
 $IMG \
 bash -c "pip install --upgrade bizyui bizyengine && python3 /app/ComfyUI/main.py --cpu --listen 0.0.0.0 --disable-metadata --port 8188"
```

**BizyDraft 拖拉拽启动**

```bash
IMG=sf-acr-registry.cn-shanghai.cr.aliyuncs.com/siliconflow/maas/bizyair-draft:v202506062349
docker run --rm --network host \
 -e BIZYAIR_SERVER_MODE=True \
 $IMG \
 bash -c "pip install --upgrade bizyui bizyengine && python3 /app/ComfyUI/main.py --cpu --listen 0.0.0.0 --disable-metadata --port 8188"
```

