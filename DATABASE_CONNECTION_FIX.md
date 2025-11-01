# 数据库连接池问题修复

## 问题描述

应用程序出现数据库连接池耗尽错误：
```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 5 reached, connection timed out, timeout 3.00
```

这表明数据库连接没有被正确释放，导致连接池耗尽。

## 根本原因

1. **依赖注入中的过早提交**: `get_current_active_device` 依赖函数在端点处理之前就提交了数据库更改
2. **手动会话管理不够健壮**: WebSocket 和后台任务中的手动会话管理缺少完善的错误处理
3. **连接池容量不足**: 在高并发场景下，连接池容量可能不够
4. **异常处理不完整**: 某些异常路径没有正确清理数据库会话

## 修复方案

### 1. 优化依赖注入 (auth.py)

**修改前:**
```python
device.last_active = datetime.now(timezone.utc)
db.commit()  # 在依赖中提交
return device
```

**修改后:**
```python
device.last_active = datetime.now(timezone.utc)
db.flush()  # 只刷新到数据库，不提交事务
return device
```

**好处:**
- 避免在依赖中提前提交
- 让端点控制事务的提交时机
- 如果端点出错，整个事务可以回滚

### 2. 添加数据库会话上下文管理器 (database.py)

**新增功能:**
```python
@contextmanager
def get_db_context() -> Session:
    """Context manager for manual database session management"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()  # 自动回滚错误
        raise
    finally:
        db.close()  # 确保会话关闭
```

**配置优化:**
```python
engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       pool_size=20,
                       max_overflow=20,  # 从 10 增加到 20
                       pool_timeout=30,
                       pool_reset_on_return='rollback',
                       pool_use_lifo=True,
                       echo_pool=False)  # 新增
```

**好处:**
- 总连接数从 25 (20+5) 增加到 40 (20+20)
- 自动处理异常时的回滚
- 确保会话总是被正确关闭

### 3. 改进 WebSocket 端点 (main.py)

**修改前:**
```python
db = next(get_db())
try:
    device = db.query(...)
    crud.activate_device(db, device_id)
finally:
    db.close()

# 异常处理分散在多个 except 块中
except WebSocketDisconnect as e:
    db = next(get_db())
    try:
        device.is_active = False
        db.commit()
    finally:
        db.close()
except Exception as e:
    # 没有清理数据库状态
    pass
```

**修改后:**
```python
try:
    with get_db_context() as db:
        device = db.query(...)
        crud.activate_device(db, device_id)
except Exception as e:
    log.error(f'Error checking device: {e}')
    await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    return

# WebSocket 循环
try:
    while True:
        data = await websocket.receive_text()
except WebSocketDisconnect as e:
    log.warning(f'websocket offline: {e}')
except Exception as e:
    log.error(f'websocket except: {e}')
finally:
    # 统一的清理逻辑
    try:
        with get_db_context() as db:
            device = db.query(...)
            if device:
                device.is_active = False
                db.commit()
    except Exception as e:
        log.error(f'Failed to deactivate device: {e}')
    finally:
        manager.disconnect(user_id, device_id)
```

**好处:**
- 使用上下文管理器自动处理会话清理
- 统一的异常处理和清理逻辑
- 确保设备状态总是被正确更新
- 所有异常路径都有适当的错误处理

### 4. 改进后台任务 (main.py)

**修改前:**
```python
db = next(get_db())
try:
    devices = db.query(...)
    # 发送通知
    await manager.send_personal_message(...)
finally:
    db.close()
```

**修改后:**
```python
try:
    with get_db_context() as db:
        devices = db.query(...)
        # 发送通知
        await manager.send_personal_message(...)
except Exception as e:
    log.error(f'Error notifying devices: {e}')
```

**好处:**
- 使用上下文管理器自动处理会话清理
- 添加了异常处理和日志记录
- 确保会话总是被释放

## 测试验证

所有修改已通过以下验证：
1. ✅ Python 语法检查 (`py_compile`)
2. ✅ 应用程序加载测试
3. ✅ 所有端点使用正确的依赖注入模式

## 预期效果

1. **连接池容量提升**: 从 25 个连接增加到 40 个连接
2. **连接泄漏修复**: 所有手动创建的会话都使用上下文管理器确保释放
3. **错误处理改进**: 所有异常路径都有适当的会话清理
4. **事务完整性**: 依赖不再过早提交，保证事务的原子性

## 注意事项

1. 需要重启应用程序以应用新配置
2. 如果仍然遇到连接池问题，可以进一步增加 `pool_size` 和 `max_overflow`
3. 监控数据库连接使用情况，确保没有长时间持有的连接

## 相关文件

- `auth.py`: 依赖注入优化
- `database.py`: 连接池配置和上下文管理器
- `main.py`: WebSocket 和后台任务的会话管理
