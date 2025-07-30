import { app } from "../../scripts/app.js";
// import { $el } from "../../scripts/ui.js";

// import { WebSocketClient } from './socket.js';



app.registerExtension({
    name: "comfy.BizyAir.Socket",

    dispatchCustomEvent(type, detail) {
        app.api.dispatchCustomEvent(type, detail);
    },

    customSocket(callback, customUrl) {
        const url = customUrl || app.api.socket.url;
        // const clientId = 'e07abdf5f465462f8dc43ca0812e9284';
        // const socket = new WebSocket(url + "?clientId=" + sessionStorage.getItem("clientId"));
        // const socket = new WebSocket(url + "?clientId=" + clientId);
        const socket = new WebSocket(url);

        const dispatchCustomEvent = this.dispatchCustomEvent;

        socket.onmessage = function (event) {
            try {
                if (event.data instanceof ArrayBuffer) {
                    const view = new DataView(event.data);
                    const eventType = view.getUint32(0);

                    let imageMime;
                    switch (eventType) {
                        case 3:
                            const decoder = new TextDecoder();
                            const data = event.data.slice(4);
                            const nodeIdLength = view.getUint32(4);
                            dispatchCustomEvent('progress_text', {
                                nodeId: decoder.decode(data.slice(4, 4 + nodeIdLength)),
                                text: decoder.decode(data.slice(4 + nodeIdLength))
                            });
                            break;
                        case 1:
                            const imageType = view.getUint32(4);
                            const imageData = event.data.slice(8);
                            switch (imageType) {
                                case 2:
                                    imageMime = 'image/png';
                                    break;
                                case 1:
                                default:
                                    imageMime = 'image/jpeg';
                                    break;
                            }
                            const imageBlob = new Blob([imageData], {
                                type: imageMime
                            });
                            dispatchCustomEvent('b_preview', imageBlob);
                            break;
                        default:
                            throw new Error(
                                `Unknown binary websocket message of type ${eventType}`
                            );
                    }
                } else {
                    const msg = JSON.parse(event.data);
                    switch (msg.type) {
                        case 'status':
                            if (msg.data.sid) {
                                const clientId = msg.data.sid;
                                window.name = clientId; // use window name so it isnt reused when duplicating tabs
                                sessionStorage.setItem('clientId', clientId); // store in session storage so duplicate tab can load correct workflow
                                socket.clientId = clientId;
                            }
                            dispatchCustomEvent('status', msg.data.status ?? null);
                            break;
                        case 'executing':
                            // msg.data.prompt_id && (msg.data.prompt_id = '');

                            dispatchCustomEvent(
                                'executing',
                                msg.data.display_node || msg.data.node
                            );
                            break;
                        case 'execution_start':
                        case 'execution_error':
                        case 'execution_interrupted':
                        case 'execution_cached':
                        case 'execution_success':
                        case 'progress':
                        case 'executed':
                        case 'graphChanged':
                        case 'promptQueued':
                        case 'logs':
                        case 'b_preview':
                            dispatchCustomEvent(msg.type, msg.data);
                            break;
                        default:
                            const registeredTypes = socket.registeredTypes || new Set();
                            const reportedUnknownMessageTypes = socket.reportedUnknownMessageTypes || new Set();

                            if (registeredTypes.has(msg.type)) {
                                app.dispatchEvent(
                                    new CustomEvent(msg.type, { detail: msg.data })
                                );
                            } else if (!reportedUnknownMessageTypes.has(msg.type)) {
                                reportedUnknownMessageTypes.add(msg.type);
                                console.warn(`Unknown message type ${msg.type}`);
                            }
                    }
                }
            } catch (error) {
                console.warn('Unhandled message:', event.data, error);
            }
        };

        socket.registeredTypes = new Set();
        socket.reportedUnknownMessageTypes = new Set();

        // 替换app.api.socket
        app.api.socket = socket;

        if (typeof callback === 'function') {
            callback(socket);
        }

        return socket;
    },

    startSocket(callback) {
        if (app.api.socket.readyState === WebSocket.CLOSED || app.api.socket.readyState === WebSocket.CLOSING) {
            return this.customSocket(callback);
        }
        return app.api.socket;
    },

    closeSocket() {
        if (app.api.socket && (app.api.socket.readyState === WebSocket.OPEN || app.api.socket.readyState === WebSocket.CONNECTING)) {
            app.api.socket.close();
            return true;
        }
        return false;
    },

    changeSocketUrl(newUrl, callback) {
        this.closeSocket();
        const clientId = sessionStorage.getItem("clientId");
        const socket = new WebSocket(newUrl + "?clientId=" + clientId + "&a=1");
        const send = app.api.socket.send;
        const onopen = app.api.socket.onopen;
        const onmessage = app.api.socket.onmessage;
        const onerror = app.api.socket.onerror;
        const onclose = app.api.socket.onclose;

        app.api.socket = socket;
        app.api.socket.send = send;
        app.api.socket.onopen = onopen;
        app.api.socket.onmessage = onmessage;
        app.api.socket.onerror = onerror;
        app.api.socket.onclose = onclose;

        if (typeof callback === 'function') {
            callback(socket);
        }

        return socket;
    },

    sendSocketMessage(message) {
        if (app.api.socket && app.api.socket.readyState === WebSocket.OPEN) {
            app.api.socket.send(typeof message === 'string' ? message : JSON.stringify(message));
            return true;
        }
        return false;
    },

    sendPrompt(prompt) {
        app.queuePrompt(prompt);
    },
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    },
    // doSendSocket() {
    //     const socket = new WebSocketClient(`/w/v1/comfy/draft/ws?clientId=${sessionStorage.getItem("clientId")
    //         }&userId=${this.getCookie("user_id")
    //         }`);
    //     const customSocket = this.customSocket.bind(this);
    //     socket.on('message', (message) => {
    //         let data = JSON.parse(message.data);
    //         if (data.status == "Running") {
    //             customSocket(() => {}, data.wsUrl);
    //         }
    //     });
    // },


    async setup() {
        const customSocket = this.customSocket.bind(this);
        const startSocket = this.startSocket.bind(this);
        const closeSocket = this.closeSocket.bind(this);
        const changeSocketUrl = this.changeSocketUrl.bind(this);
        const sendSocketMessage = this.sendSocketMessage.bind(this);
        // let iTimer = null;

        // // 直接检查一次
        // const initialUserId = this.getCookie("user_id");
        // if (initialUserId) {
        //     // 初始检查到 userId
        //     this.doSendSocket();
        // }

        // // 使用定时器监听cookie变化
        // let lastCookieValue = this.getCookie("user_id");
        // iTimer = setInterval(() => {
        //     const currentCookieValue = this.getCookie("user_id");
        //     if (currentCookieValue && currentCookieValue !== lastCookieValue) {
        //         // 检测到 cookie user_id 变化
        //         lastCookieValue = currentCookieValue;
        //         this.doSendSocket();
        //         clearInterval(iTimer);
        //     }
        // }, 300); // 每秒检查一次

        const methods = {
            customSocket: function (params) {
                const callback = params.callback ? new Function('socket', params.callback) : null;
                const socket = customSocket(callback, params.url);
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'customSocket',
                    result: '自定义socket执行结果'
                }, '*');
                return socket;
            },

            startSocket: function (params) {
                const callback = params.callback ? new Function('socket', params.callback) : null;
                const socket = startSocket(callback);
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'startSocket',
                    result: 'Socket连接已启动'
                }, '*');
                return socket;
            },

            closeSocket: function () {
                const result = closeSocket();
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'closeSocket',
                    result: result ? 'Socket连接已关闭' : 'Socket连接关闭失败或已关闭'
                }, '*');
                return result;
            },

            changeSocketUrl: function (params) {
                if (!params.url) {
                    console.error('缺少url参数');
                    return false;
                }
                const callback = params.callback ? new Function('socket', params.callback) : null;
                const socket = changeSocketUrl(params.url, callback);
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'changeSocketUrl',
                    result: 'Socket URL已更改为' + params.url
                }, '*');
                return socket;
            },

            sendSocketMessage: function (params) {
                if (!params.message) {
                    console.error('缺少message参数');
                    return false;
                }
                const result = sendSocketMessage(params.message);
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'sendSocketMessage',
                    result: result ? '消息发送成功' : '消息发送失败'
                }, '*');
                return result;
            },

            clearCanvas: function () {
                app.graph.clear();
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'clearCanvas',
                    result: true
                }, '*');
                return true;
            },

            loadWorkflow: function (params) {
                app.graph.clear();
                if (params.json.version) {
                    app.loadGraphData(params.json);
                } else {
                    app.loadApiJson(params.json, 'bizyair');
                }
                console.log("-----------loadWorkflow-----------", params.json)
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'loadWorkflow',
                    result: true
                }, '*');
                return true;
            },

            saveWorkflow: async function () {
                const graph = await app.graphToPrompt();
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'saveWorkflow',
                    result: graph.workflow
                }, '*');
                return graph.workflow;
            },
            getWorkflow: async function () {
                const graph = await app.graphToPrompt();
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'getWorkflow',
                    result: graph.workflow
                }, '*');
                return graph.workflow;
            },
            saveApiJson: async function (params) {
                const graph = await app.graphToPrompt();
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'saveApiJson',
                    result: graph.output
                }, '*');
                return graph.output;
            },
            getClientId: function () {
                const clientId = sessionStorage.getItem("clientId");
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'getClientId',
                    result: clientId
                }, '*');
                return clientId;
            },
            runWorkflow: async function () {
                const graph = await app.graphToPrompt();
                const res = await app.queuePrompt(graph.output);
                console.log("-----------queuePrompt-----------", res)
                const clientId = sessionStorage.getItem("clientId");
                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'runWorkflow',
                    result: {
                        clientId: clientId,
                        jsonWorkflow: graph.output,
                        workflow: graph.workflow
                    }
                }, '*');
                return true;
            },
            setCookie: function (params) {
                const setCookie = (name, value, days) => {
                    let expires = "";
                    if (days) {
                        const date = new Date();
                        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                        expires = "; expires=" + date.toUTCString();
                    }
                    document.cookie = name + "=" + (value || "") + expires + "; path=/";
                };
                console.log("-----------setCookie-----------", params)
                setCookie(params.name, params.value, params.days);
                // window.parent.postMessage({
                //     type: 'functionResult',
                //     method: 'setCookie',
                //     result: true
                // }, '*');
                return true;
            },
            fitView: function () {
                // window.app.canvas.ds.offset = [0, 0];
                // window.app.canvas.ds.scale = 1;
                // window.app.canvas.setDirty(true, true);
                app.canvas.fitViewToSelectionAnimated()

                window.parent.postMessage({
                    type: 'functionResult',
                    method: 'fitView',
                    result: true
                }, '*');
                return true;
            }
        };

        window.addEventListener('message', function (event) {
            if (event.data && event.data.type === 'callMethod') {
                const methodName = event.data.method;
                const params = event.data.params || {};

                if (methods[methodName]) {
                    methods[methodName](params);
                } else {
                    console.error('方法不存在:', methodName);
                }
            }
        });
        window.parent.postMessage({ type: 'iframeReady' }, '*');
    }
});
