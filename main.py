import time
import utils


# 界面识别配置: (模板路径, 界面名称)
INTERFACE_CONFIGS = [
    (r"templates\活动场-游戏主界面.png", "游戏主界面"),
    (r"templates\闲趣百市-活动场界面.png", "活动场界面"),
    (r"templates\阿超钓鱼-闲趣百市界面.png", "闲趣百市界面"),
    (r"templates\开始钓鱼-阿超钓鱼界面.png", "阿超钓鱼界面"),
]

# 界面点击配置: {界面名称: 点击的模板路径}
CLICK_CONFIGS = {
    "游戏主界面": r"templates\活动场-游戏主界面.png",
    "活动场界面": r"templates\闲趣百市-活动场界面.png",
}


_current_interface = None


def recognize_interface():
    for template_path, interface_name in INTERFACE_CONFIGS:
        matches = utils.find_template(template_path)
        if matches:
            return interface_name
    return None


def main():
    global _current_interface
    
    utils.logger.info("自动钓鱼程序启动")
    
    while True:
        interface = recognize_interface()
        
        if interface != _current_interface:
            if interface:
                utils.logger.info(f"界面切换: -> {interface}")
            else:
                utils.logger.info(f"界面切换: -> 未知界面")
            _current_interface = interface
        
        # 如果识别到已知界面，执行点击
        if interface in CLICK_CONFIGS:
            template_path = CLICK_CONFIGS[interface]
            utils.find_and_click(template_path)
            time.sleep(1)  # 点击后等待界面切换
        
        time.sleep(1)


if __name__ == "__main__":
    main()
