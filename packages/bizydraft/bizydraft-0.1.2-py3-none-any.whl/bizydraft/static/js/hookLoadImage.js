import { app } from "../../scripts/app.js";
import { fileToOss } from "./uploadFile.js";
import { getCookie } from './tool.js';

app.registerExtension({
    name: "bizyair.image.to.oss",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === 'LoadImage') {
            nodeType.prototype.onNodeCreated = async function() {
                // const apiHost = 'http://localhost:3000/api'
                const apiHost = 'https://uat87.bizyair.cn/api'
                const getData = async () => {
                    const res = await fetch(`${apiHost}/community/commit_input_resource?${
                        new URLSearchParams({
                            url: '',
                            ext: '',
                            current: 1,
                            page_size: 100

                        }).toString()
                    }`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${getCookie('bizy_token')}`
                        }
                    })
                    const {data} = await res.json()
                    const list = data.data.data.list || []
                    const image_list = list.filter(item => item.name).map(item => {
                        return {
                            url: item.url,
                            name: item.name
                        }
                        // return item.url
                    })
                    const image_widget = this.widgets.find(w => w.name === 'image');
                    
                    const node = this;

                    image_widget.options.values = image_list.map(item => item.name);
                    
                    // image_widget.value = image_list[0].url;
                    // image_widget.value = image_list[0];
                    if (image_list[0] && image_list[0].url) {
                        previewImage(node, decodeURIComponent(image_list[0].url))
                    }
                    image_widget.callback = function(e) {
                        const image_url = decodeURIComponent(image_list.find(item => item.name === e).url);
                        previewImage(node, image_url)
                    }
                }
                getData()
                

                const upload_widget = this.widgets.find(w => w.name === 'upload');
                upload_widget.callback = async function() {
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.accept = 'image/*';
                    input.onchange = async (e) => {
                        const file = e.target.files[0];
                        await fileToOss(file);

                        getData()
                    }
                    input.click();
                }
            }
        }
    }
})

function previewImage(node, image_url) {
    const img = new Image();
    img.onload = function() {
        node.imgs = [img];
        if (node.graph) {
            node.graph.setDirtyCanvas(true);
        } else {
            console.warn('[BizyAir] 无法访问graph对象进行重绘');
        }
        const imageOutputStore = 
            node.nodeOutputStore || 
            window.app?.nodeOutputStore || 
            app?.nodeOutputStore;
            
        if (imageOutputStore) {
            console.log('[BizyAir] 设置节点输出数据');
            imageOutputStore.setNodeOutputs(node, image_url, { isAnimated: false });
        } else {
            console.warn('[BizyAir] 未找到nodeOutputStore');
        }
    };
    img.onerror = function(err) {
        console.error('[BizyAir] 图片加载失败:', image_url, err);
    };
    img.src = image_url;
}
