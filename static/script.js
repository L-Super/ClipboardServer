// 全局变量
let currentForm = 'login';
let currentLoginMethod = 'password'; // 'password' 或 'code'
let codeCountdown = 0; // 验证码倒计时

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function () {
    // 绑定表单提交事件
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);

    // 生成默认设备ID
    generateDeviceId();

    // 绑定设备名称生成按钮事件
    document.getElementById('generateDeviceNameBtn').addEventListener('click', generateDeviceName);
});

// 切换表单显示
function switchForm(formType) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (formType === 'register') {
        loginForm.classList.remove('active');
        registerForm.classList.add('active');
        currentForm = 'register';
    } else {
        registerForm.classList.remove('active');
        loginForm.classList.add('active');
        currentForm = 'login';
    }
}

// 切换登录方式
function switchLoginMethod(method) {
    currentLoginMethod = method;
    const passwordBtn = document.getElementById('passwordLoginBtn');
    const codeBtn = document.getElementById('codeLoginBtn');
    const passwordArea = document.getElementById('passwordLoginArea');
    const codeArea = document.getElementById('codeLoginArea');
    const passwordInput = document.getElementById('loginPassword');
    const codeInput = document.getElementById('loginCode');

    if (method === 'password') {
        passwordBtn.classList.add('active');
        codeBtn.classList.remove('active');
        passwordArea.style.display = 'block';
        codeArea.style.display = 'none';
        passwordInput.required = true;
        codeInput.required = false;
        codeInput.value = '';
    } else {
        passwordBtn.classList.remove('active');
        codeBtn.classList.add('active');
        passwordArea.style.display = 'none';
        codeArea.style.display = 'block';
        passwordInput.required = false;
        codeInput.required = true;
        passwordInput.value = '';
    }
}

// 浏览器端设备指纹生成
async function generateDeviceFingerprint() {
    const fingerprint = {
        userAgent: navigator.userAgent,
        screen: `${screen.width}x${screen.height}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        languages: navigator.languages.join(','),
        hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
        deviceMemory: navigator.deviceMemory || 'unknown',
        platform: navigator.userAgentData?.platform || navigator.platform || 'unknown',
        // 添加Canvas指纹
        canvasHash: await generateCanvasFingerprint(),
        // WebGL指纹
        webglHash: await generateWebGLFingerprint(),
        // 其他可收集的稳定特征
    };

    // 生成SHA-256哈希作为设备指纹
    const fingerprintString = JSON.stringify(fingerprint);
    const hashBuffer = await crypto.subtle.digest('SHA-256',
        new TextEncoder().encode(fingerprintString));
    return Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, '0')).join('');
}

// 生成Canvas指纹
async function generateCanvasFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('DeviceFingerprint@2023', 2, 2);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    return Array.from(imageData.data).join('');
}

// 生成WebGL指纹
async function generateWebGLFingerprint() {
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (!gl) return 'webgl_not_supported';

        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (!debugInfo) return 'debug_info_not_supported';

        const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
        const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);

        return `${vendor}|${renderer}`;
    } catch (error) {
        return 'webgl_error';
    }
}

// 生成设备ID（隐藏字段）
async function generateDeviceId() {
    // 创建一个隐藏的输入字段来存储设备指纹
    let hiddenDeviceId = document.getElementById('hiddenDeviceId');
    if (!hiddenDeviceId) {
        hiddenDeviceId = document.createElement('input');
        hiddenDeviceId.type = 'hidden';
        hiddenDeviceId.id = 'hiddenDeviceId';
        document.getElementById('loginForm').appendChild(hiddenDeviceId);
    }
    hiddenDeviceId.value = await generateDeviceFingerprint();
}

// 显示消息提示
function showMessage(text, type = 'info') {
    const message = document.getElementById('message');
    const messageText = document.getElementById('messageText');

    message.className = `message ${type}`;
    messageText.textContent = text;
    message.style.display = 'flex';

    // 5秒后自动隐藏
    setTimeout(() => {
        hideMessage();
    }, 5000);
}

// 隐藏消息提示
function hideMessage() {
    document.getElementById('message').style.display = 'none';
}

// 设置按钮加载状态
function setButtonLoading(button, loading) {
    const btnText = button.querySelector('.btn-text');
    const btnLoading = button.querySelector('.btn-loading');

    if (loading) {
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline-block';
        button.disabled = true;
    } else {
        btnText.style.display = 'inline-block';
        btnLoading.style.display = 'none';
        button.disabled = false;
    }
}

// 发送验证码
async function sendVerificationCode() {
    const email = document.getElementById('loginEmail').value;
    const sendBtn = document.getElementById('sendCodeBtn');

    // 验证邮箱格式
    if (!email) {
        showMessage('请先输入邮箱地址', 'error');
        return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMessage('请输入有效的邮箱地址', 'error');
        return;
    }

    // 如果正在倒计时，不允许重复发送
    if (codeCountdown > 0) {
        return;
    }

    // 设置按钮加载状态
    const btnText = sendBtn.querySelector('.btn-text');
    const originalText = btnText.textContent;
    sendBtn.disabled = true;
    btnText.textContent = '发送中...';

    try {
        const response = await fetch('/auth/send-verification-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('验证码已发送，请查收邮件', 'success');
            // 开始倒计时
            startCodeCountdown();
        } else {
            const errorMsg = data.detail || (data.error && data.error.message) || '发送验证码失败';
            showMessage(errorMsg, 'error');
            // 恢复按钮状态
            sendBtn.disabled = false;
            btnText.textContent = originalText;
        }
    } catch (error) {
        console.error('发送验证码错误:', error);
        showMessage('网络错误，请稍后重试', 'error');
        // 恢复按钮状态
        sendBtn.disabled = false;
        btnText.textContent = originalText;
    }
}

// 验证码倒计时
function startCodeCountdown() {
    codeCountdown = 60; // 60秒倒计时
    const sendBtn = document.getElementById('sendCodeBtn');
    const btnText = sendBtn.querySelector('.btn-text');

    sendBtn.disabled = true;

    const timer = setInterval(() => {
        codeCountdown--;
        if (codeCountdown > 0) {
            btnText.textContent = `${codeCountdown}秒后重发`;
        } else {
            clearInterval(timer);
            btnText.textContent = '发送验证码';
            sendBtn.disabled = false;
        }
    }, 1000);
}

// 处理登录
async function handleLogin(e) {
    e.preventDefault();

    const button = e.target.querySelector('button[type="submit"]');
    setButtonLoading(button, true);

    try {
        const email = document.getElementById('loginEmail').value;
        const deviceId = document.getElementById('hiddenDeviceId').value;
        const deviceName = document.getElementById('loginDeviceName').value;
        const deviceType = getDeviceType();

        // 验证必填字段
        if (!email || !deviceId || !deviceName || !deviceType) {
            showMessage('请填写所有必填字段', 'error');
            return;
        }

        let response;
        let data;

        if (currentLoginMethod === 'password') {
            // 密码登录
            const password = document.getElementById('loginPassword').value;
            if (!password) {
                showMessage('请填写所有必填字段', 'error');
                return;
            }

            response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    device_id: deviceId,
                    device_name: deviceName,
                    device_type: deviceType
                })
            });
        } else {
            // 验证码登录
            const code = document.getElementById('loginCode').value;
            if (!code) {
                showMessage('请填写所有必填字段', 'error');
                return;
            }

            response = await fetch('/auth/login-with-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    code: code,
                    device_id: deviceId,
                    device_name: deviceName,
                    device_type: deviceType
                })
            });
        }

        data = await response.json();

        if (response.ok) {
            showMessage('登录成功！', 'success');

            // 保存token到localStorage
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('email', email);
            localStorage.setItem('device_name', deviceName);

            const apiUrl = `${window.location.origin}`;
            let protocol_url = `floward://login?email=${encodeURIComponent(email)}&token=${encodeURIComponent(data.access_token)}&device_name=${encodeURIComponent(deviceName)}&api_url=${encodeURIComponent(apiUrl)}`
            try {
                window.location.href = protocol_url;
            } catch (error) {
                console.error('Error:', error);
            }
            // 延迟跳转到主页面
            setTimeout(() => {
                window.location.href = '/dashboard';
            });
        } else {
            const errorMsg = data.detail || (data.error && data.error.message) || '登录失败，请检查输入信息';
            showMessage(errorMsg, 'error');
        }
    } catch (error) {
        console.error('登录错误:', error);
        showMessage('网络错误，请稍后重试', 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

// 处理注册
async function handleRegister(e) {
    e.preventDefault();

    const button = e.target.querySelector('button[type="submit"]');
    setButtonLoading(button, true);

    try {
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('registerConfirmPassword').value;

        // 验证必填字段
        if (!email || !password || !confirmPassword) {
            showMessage('请填写所有必填字段', 'error');
            return;
        }

        // 验证密码确认
        if (password !== confirmPassword) {
            showMessage('两次输入的密码不一致', 'error');
            return;
        }

        // 验证密码长度
        if (password.length < 6) {
            showMessage('密码长度至少6位', 'error');
            return;
        }

        // 验证邮箱格式
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showMessage('请输入有效的邮箱地址', 'error');
            return;
        }

        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('注册成功！请登录', 'success');

            // 切换到登录表单
            setTimeout(() => {
                switchForm('login');
                // 自动填充邮箱
                document.getElementById('loginEmail').value = email;
            }, 1500);
        } else {
            // 针对后端返回的"Email already registered"错误进行特殊处理
            if (
                (data.detail && data.detail === "Email already registered") ||
                (data.error && data.error.message === "Email already registered")
            ) {
                showMessage('该邮箱已被注册，请更换邮箱', 'error');
            } else {
                showMessage(
                    (data.detail || (data.error && data.error.message)) || '注册失败，请稍后重试',
                    'error'
                );
            }
        }
    } catch (error) {
        console.error('注册错误:', error);
        showMessage('网络错误，请稍后重试', 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

// 实时验证密码确认
document.getElementById('registerConfirmPassword').addEventListener('input', function () {
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = this.value;

    if (confirmPassword && password !== confirmPassword) {
        this.style.borderColor = '#f44336';
    } else {
        this.style.borderColor = '#e1e5e9';
    }
});

// 实时验证邮箱格式
document.getElementById('registerEmail').addEventListener('input', function () {
    const email = this.value;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (email && !emailRegex.test(email)) {
        this.style.borderColor = '#f44336';
    } else {
        this.style.borderColor = '#e1e5e9';
    }
});

// 生成设备名称按钮点击事件
function generateDeviceName() {
    const deviceNameInput = document.getElementById('loginDeviceName');
    deviceNameInput.value = getDeviceName();

    // 显示提示信息
    showMessage('设备名称已自动生成', 'success');
}


// 检测设备类型
function getDeviceType() {
    const ua = navigator.userAgent.toLowerCase();
    const platform = (navigator.userAgentData?.platform || navigator.platform || '').toLowerCase();

    // 定义映射表
    const deviceTypeMap = [
        {pattern: /android/, type: 'android'},
        {pattern: /iphone|ipad|ipod/, type: 'ios'},
        {pattern: /windows/, type: 'windows'},
        {pattern: /macintosh|mac os x/, type: 'macos'},
        {pattern: /linux/, type: 'linux'}
    ];

    // 优先检测 userAgent
    for (const item of deviceTypeMap) {
        if (item.pattern.test(ua)) {
            return item.type;
        }
    }
    // 再检测 platform
    for (const item of deviceTypeMap) {
        if (item.pattern.test(platform)) {
            return item.type;
        }
    }
    // 默认返回 web
    return 'web';
}

// 自动生成友好设备名
function getDeviceName() {
    let deviceType;
    if (/Mobi|Android/i.test(navigator.userAgent)) deviceType = 'Mobile';
    if (/Tablet|iPad/i.test(navigator.userAgent)) deviceType = 'Tablet';
    else deviceType = 'Desktop';

    const platform = navigator.userAgentData?.platform || navigator.platform || 'unknown';
    return `${deviceType} on ${platform}`;
}
