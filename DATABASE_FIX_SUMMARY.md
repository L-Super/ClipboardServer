# 数据库连接池问题修复总结

## 问题描述

应用程序在运行过程中遇到以下错误：
1. `QueuePool limit of size 20 overflow 5 reached, connection timed out` - 连接池耗尽
2. `BrokenPipeError: [Errno 32] Broken pipe` - MySQL连接断开
3. `MySQL server has gone away` - MySQL服务器连接丢失

## 根本原因

### 1. WebSocket连接中的数据库会话泄漏（主要问题）
- `websocket_endpoint` 函数通过 `Depends(get_db)` 注入数据库会话
- 该会话在整个WebSocket连接生命周期内保持打开（可能持续数小时甚至数天）
- 导致：
  - 连接池中的连接永远不会被释放
  - MySQL连接超时（默认 `wait_timeout` 是8小时）
  - 当MySQL关闭超时连接时出现 BrokenPipeError

### 2. 后台任务中的会话管理问题
- `notify_devices_of_update` 函数接收从请求上下文传递的 `db` 会话
- 当后台任务执行时，原始请求可能已经结束，会话可能已经关闭

## 修复方案

### 1. WebSocket端点 (main.py)
**修改前：**
```python
@app.websocket("/sync/notify")
async def websocket_endpoint(
        websocket: WebSocket,
        token: str,
        db: Session = Depends(get_db)  # ❌ 整个连接期间持有会话
):
    device = db.query(models.Device).filter(...).first()
    crud.activate_device(db, device_id)
    # ... WebSocket循环 ...
```

**修改后：**
```python
@app.websocket("/sync/notify")
async def websocket_endpoint(
        websocket: WebSocket,
        token: str  # ✅ 不再注入数据库会话
):
    # ✅ 需要时创建临时会话
    db = next(get_db())
    try:
        device = db.query(models.Device).filter(...).first()
        crud.activate_device(db, device_id)
    finally:
        db.close()  # ✅ 立即关闭会话
    
    # WebSocket循环不持有任何数据库连接
    try:
        while True:
            data = await websocket.receive_text()
            # ...
    except WebSocketDisconnect as e:
        # ✅ 断开时使用新的临时会话
        db = next(get_db())
        try:
            device = db.query(models.Device).filter(...).first()
            if device:
                device.is_active = False
                db.commit()
        finally:
            db.close()
```

### 2. 后台任务 (main.py)
**修改前：**
```python
# 调用处
background_tasks.add_task(
    notify_devices_of_update,
    current_user.id,
    current_device.id,
    db_item,
    db  # ❌ 传递请求的会话
)

# 函数定义
async def notify_devices_of_update(user_id: str, source_device_id: str, 
                                  item: models.ClipboardItem, db: Session):
    devices = db.query(models.Device).filter(...).all()
    # ...
```

**修改后：**
```python
# 调用处
background_tasks.add_task(
    notify_devices_of_update,
    current_user.id,
    current_device.id,
    db_item  # ✅ 不传递会话
)

# 函数定义
async def notify_devices_of_update(user_id: str, source_device_id: str, 
                                  item: models.ClipboardItem):
    # ✅ 创建新的会话
    db = next(get_db())
    try:
        devices = db.query(models.Device).filter(...).all()
        # ...
    finally:
        db.close()  # ✅ 确保会话关闭
```

### 3. 数据库连接池配置优化 (database.py)
**修改前：**
```python
engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       pool_recycle=1800,      # 30分钟
                       pool_pre_ping=True,
                       pool_size=20,
                       max_overflow=5,          # 溢出连接少
                       pool_timeout=3,          # 超时时间短
                       pool_reset_on_return=True,
                       pool_use_lifo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

**修改后：**
```python
engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       pool_recycle=3600,       # ✅ 1小时（小于MySQL的wait_timeout）
                       pool_pre_ping=True,      # ✅ 使用前ping检查连接
                       pool_size=20,            # 连接池大小
                       max_overflow=10,         # ✅ 增加溢出连接数
                       pool_timeout=30,         # ✅ 增加超时时间
                       pool_reset_on_return='rollback',  # ✅ 归还时回滚
                       pool_use_lifo=True)      # ✅ LIFO提高连接复用
SessionLocal = sessionmaker(autocommit=False, autoflush=False, 
                          bind=engine, expire_on_commit=False)  # ✅ 防止提交后对象失效
```

## 修复效果

1. **解决连接池耗尽**：WebSocket连接不再长期占用数据库连接
2. **解决BrokenPipe错误**：数据库连接及时释放，不会超时
3. **提高系统稳定性**：后台任务使用独立会话，不受请求生命周期影响
4. **优化连接管理**：更合理的连接池配置

## 最佳实践建议

1. **WebSocket中避免长期持有数据库会话**
   - 仅在需要数据库操作时创建临时会话
   - 操作完成后立即关闭会话

2. **后台任务使用独立会话**
   - 不要传递请求的数据库会话给后台任务
   - 在后台任务中创建新的会话

3. **合理配置连接池**
   - `pool_recycle` 应小于数据库的 `wait_timeout`
   - `pool_pre_ping=True` 确保连接可用
   - 根据实际负载调整 `pool_size` 和 `max_overflow`

4. **使用上下文管理器或try-finally确保会话关闭**
   ```python
   db = next(get_db())
   try:
       # 数据库操作
   finally:
       db.close()
   ```
