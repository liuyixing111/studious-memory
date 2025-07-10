import RPi.GPIO as GPIO
import time

# 硬件引脚配置 (根据你的接线修改)
LED_PIN = 17      # 控制LED的GPIO引脚
SERVO_PIN = 18    # 控制舵机的GPIO引脚

# 舵机参数 (根据你的舵机规格调整)
SERVO_MIN_DUTY = 2.5   # 0度时的占空比
SERVO_MAX_DUTY = 12.5   # 180度时的占空比

def setup():
    """初始化硬件配置"""
    GPIO.setmode(GPIO.BCM)
    
    # 初始化LED引脚
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.LOW)
    
    # 初始化舵机PWM
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    global servo_pwm
    servo_pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz频率
    servo_pwm.start(0)

def control_light(state):
    """控制LED灯开关
    Args:
        state (bool): True开灯，False关灯
    """
    GPIO.output(LED_PIN, GPIO.HIGH if state else GPIO.LOW)

def control_servo(angle):
    """控制舵机转动到指定角度
    Args:
        angle (int): 0-180之间的角度值
    """
    angle = max(0, min(180, angle))  # 限制角度范围
    duty_cycle = SERVO_MIN_DUTY + (angle / 180) * (SERVO_MAX_DUTY - SERVO_MIN_DUTY)
    servo_pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)  # 等待舵机转动到位
    servo_pwm.ChangeDutyCycle(0)  # 停止发送PWM信号防止抖动

def cleanup():
    """清理GPIO资源"""
    servo_pwm.stop()
    GPIO.cleanup()

# 使用示例 ----------------------------
if __name__ == "__main__":
    try:
        setup()
        
        # 测试LED控制
        control_light(True)  # 开灯
        time.sleep(2)
        control_light(False)  # 关灯
        
        # 测试舵机控制
        control_servo(0)     # 转到0度
        time.sleep(1)
        control_servo(90)    # 转到90度
        time.sleep(1)
        control_servo(180)   # 转到180度
        
    finally:
        cleanup()