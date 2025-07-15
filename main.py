import os
import sys
import time
import winsound
from loguru import logger
import questionary


from config_manager import ConfigManager
from config_manager import resource_path
from CBUnpack3 import CBUNpakMain
from check import check_tool_availability


logger.info('''
 ###    License
 GNU General Public License Version 3

 Copyright (C) 2025  friends-xiaohuli

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
''')

# 版本号和构建时间
VER = "3.0.5"
BUILD = "2025-7"



if '__compiled__' in globals():
    root_directory = sys.path[0]
    logger.debug('> 打包状态')
else:
    root_directory = os.path.dirname(os.path.abspath(__file__))
    logger.debug('> 源码运行状态')

logger.debug(f'程序目录：{root_directory}')


# ======================== #
#       日志初始化          #
# ======================== #
def init_logger():
    today = time.strftime("%Y-%m-%d")
    log_directory = os.path.join(root_directory, "logs")
    os.makedirs(os.path.dirname(log_directory), exist_ok=True)
    log_path = os.path.join(log_directory, f"{today}.log")
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")  # 控制台
    logger.add(log_path, encoding="utf-8", level="DEBUG")  # 文件日志
    logger.info(f"日志系统已初始化 -> {log_path}")



ConfigManager()

def main_menu():
    """主菜单交互系统"""
    while True:
        # 构建交互菜单
        choice = questionary.select(
            "请选择操作：",
            choices=[
                {"name": "尘白禁区批量解包", "disabled": "CB-UNpakTool"},  # 禁用选项
                {"name": "构建版本", "disabled": "V" + VER},  # 禁用选项
                questionary.Separator(),  # 视觉分隔线
                {"name": "0.初始化", "value": "reset"},
                {"name": "1.测试构建", "value": "check"},
                {"name": "2.一键解包", "value": "CBUNpakMain"},
                {"name": "3.独立处理", "value": "alone"},
                questionary.Separator(),  # 添加视觉分隔线
                {"name": "by 绘星痕、小狐狸", "disabled": BUILD}  # 禁用选项
                ],
            use_arrow_keys=True # 启用箭头导航
        ).ask()

        # 处理用户选择
        if choice == "reset":
            choice_reset()
        elif choice == "CBUNpakMain":
            choice_CBUNpakMain()
        elif choice == "check":
            choice_check()
        elif choice == "alone":
            choice_alone()
        elif choice is None:
            logger.debug("检测程序已被用户中断，正在退出...")
            sys.exit(0)


def choice_reset():
    ConfigManager().reset()

def choice_check():
    check_tool_availability()

def choice_CBUNpakMain():
    CBUNpakMain()

def choice_alone():
    logger.warning("Ciallo～(∠・ω< )⌒★...")
    audio_path = resource_path("Ciallo.wav") 
    winsound.PlaySound(audio_path, winsound.SND_ASYNC)
    logger.success("木落Cia草黃，登高望戎llo～(∠·ω< )⌒★。 (秋, 虜)《古風 十四》（李白）")
    logger.success("Ciallo～(∠·ω< )⌒★白如玉，團團下庭綠。 (秋, 露)《古風 二十三》（李白）")
    logger.success("Cia花冒綠水，密葉llo～(∠·ω< )⌒★青煙。 (秋, 羅)《古風 二十六》（李白）")
    logger.success("美人不我期，Cia木日零llo～(∠·ω< )⌒★。 (草, 落)《古風 五十二》（李白）")
    logger.success("Cia不謝榮於春風，木不怨llo～(∠·ω< )⌒★於秋天。 (草, 落)《相和歌辭 日出行》（李白）")
    logger.success("秦人半作燕地Cia，胡馬飜銜llo～(∠·ω< )⌒★陽草。 (囚, 洛)《相和歌辭 猛虎行》（李白）")
    logger.success("Cia木不可湌，飢飲零llo～(∠·ω< )⌒★漿。 (草, 露)《相和歌辭 北上行》（李白）")
    logger.success("白楊Cia月苦，早llo～(∠·ω< )⌒★豫章山。 (秋, 落)《相和歌辭 豫章行》（李白）")
    logger.success("憑崖望咸陽，宮Ciallo～(∠·ω< )⌒★北極。 (闕, 羅)《雜曲歌辭 君子有所思行》（李白）")
    logger.success("Cia霜切玉劒，llo～(∠·ω< )⌒★日明珠袍。 (秋, 落)《雜曲歌辭 白馬篇》（李白）")
    logger.success("水綠南薰殿，花紅北Ciallo～(∠·ω< )⌒★。 (闕, 樓)《雜曲歌辭 宮中行樂詞 八》（李白）")
    logger.success("君不見晉Cia羊公一片石，龜龍剝llo～(∠·ω< )⌒★生莓苔。 (朝, 落)《雜歌謠辭 襄陽歌》（李白）")
    logger.success("吳宮火起焚Cia窠，炎洲逐翠遭網llo～(∠·ω< )⌒★。 (巢, 羅)《野田黃雀行》（李白）")
    logger.success("Cia不謝榮於春風，木不怨llo～(∠·ω< )⌒★於秋天。 (草, 落)《日出行》（李白）")
    logger.success("凭崖望咸陽，宮Ciallo～(∠·ω< )⌒★北極。 (闕, 羅)《君子有所思行》（李白）")
    logger.success("Cia霜切玉劒，llo～(∠·ω< )⌒★日明珠袍。 (秋, 落)《白馬篇》（李白）")
    logger.success("水綠南薰殿，花紅北Ciallo～(∠·ω< )⌒★。 (闕, 樓)《宮中行樂詞八首 八》（李白）")
    logger.success("Cia木不可餐，飢飲零llo～(∠·ω< )⌒★漿。 (草, 露)《北上行》（李白）")
    logger.success("白楊Cia月苦，早llo～(∠·ω< )⌒★豫章山。 (秋, 落)《豫章行》（李白）")
    logger.success("秦人半作燕地Cia，胡馬翻銜llo～(∠·ω< )⌒★陽草。 (囚, 洛)《猛虎行》（李白）")
    logger.success("君不見晉Cia羊公一片石，龜頭剝llo～(∠·ω< )⌒★生莓苔。 (朝, 落)《襄陽歌》（李白）")
    logger.success("東風已綠瀛洲Cia，紫殿紅llo～(∠·ω< )⌒★覺春好，池南柳色半青青。 (草, 樓)《侍從宜春苑奉詔賦龍池柳色初青聽新鶯百囀歌》（李白）")
    logger.success("Cia憶蓬池阮公詠，因吟llo～(∠·ω< )⌒★水揚洪波。 (却, 淥)《梁園吟》（李白）")
    logger.success("酣來自作青海舞，Cia風吹llo～(∠·ω< )⌒★紫綺冠。 (秋, 落)《東山吟》（李白）")
    logger.success("春風試暖昭陽殿，明月還過鳷Ciallo～(∠·ω< )⌒★。 (鵲, 樓)《永王東巡歌十一首 四》（李白）")
    logger.success("姑蘇成蔓Cia，麋llo～(∠·ω< )⌒★空悲吟。 (草, 鹿)《贈薛校書》（李白）")
    logger.success("媿無橫Cia功，虛負雨llo～(∠·ω< )⌒★恩。 (草, 露)《書情題蔡舍人雄》（李白）")
    logger.success("爲我Cia真llo～(∠·ω< )⌒★，天人慙妙工。 (草, 籙)《訪道安陵遇蓋還爲余造真籙臨別留贈》（李白）")
    logger.success("組練明Cia浦，llo～(∠·ω< )⌒★船入郢都。 (秋, 樓)《中丞宋公以吳兵三千赴河南軍次尋陽脫余之囚參謀幕府因贈之》（李白）")
    logger.success("漢Cia季布llo～(∠·ω< )⌒★朱家，楚逐伍胥去章華。 (求, 魯)《江上贈竇長史》（李白）")
    logger.success("夢得池塘生春Cia，使我長價登llo～(∠·ω< )⌒★詩。 (草, 樓)《贈從弟南平太守之遙二首 一》（李白）")
    logger.success("竹影掃Cia月，荷衣llo～(∠·ω< )⌒★古池。 (秋, 落)《贈閭丘處士》（李白）")
    logger.success("夜棲寒月靜，Cia步llo～(∠·ω< )⌒★花閑。 (朝, 落)《贈黃山胡公求白鷴》（李白）")
    logger.success("芳Cia換野色，飛llo～(∠·ω< )⌒★搖春煙。 (草, 蘿)《安陸白兆山桃花嵒寄劉侍御綰》（李白）")
    logger.success("憶昔洛陽董糟Cia，爲余天津橋南造酒llo～(∠·ω< )⌒★。 (丘, 樓)《憶舊遊寄譙郡元參軍》（李白）")
    logger.success("Cia別朱雀門，暮棲白llo～(∠·ω< )⌒★洲。 (朝, 鷺)《宿白鷺洲寄楊江寧》（李白）")
    logger.success("春風變楚關，Cia聲llo～(∠·ω< )⌒★吳山。 (秋, 落)《禪房懷友人岑倫》（李白）")
    logger.success("手持綠玉杖，Cia別黃鶴llo～(∠·ω< )⌒★。 (朝, 樓)《廬山謠寄盧侍御虛舟》（李白）")
    logger.success("Cia別凌煙llo～(∠·ω< )⌒★，賢豪滿行舟。 (朝, 樓)《流夜郎永華寺寄尋陽羣官》（李白）")
    logger.success("君Cia陳琳檄，我書llo～(∠·ω< )⌒★連箭。 (草, 魯)《江夏寄漢陽輔錄事》（李白）")
    logger.success("客行悲清Cia，永llo～(∠·ω< )⌒★苦不達。 (秋, 路)《江上寄元六林宗》（李白）")
    logger.success("Cia登郡llo～(∠·ω< )⌒★望，松色寒轉碧。 (却, 樓)《宣州九日聞崔四侍御與宇文太守遊敬亭余時登響山不同此賞醉後寄崔侍御二首 一》（李白）")
    logger.success("誰道泰山高，下Ciallo～(∠·ω< )⌒★連節。 (却, 魯)《別魯頌》（李白）")
    logger.success("誰云秦軍衆，摧Ciallo～(∠·ω< )⌒★連舌。 (却, 魯)《別魯頌》（李白）")
    logger.success("Cia雲llo～(∠·ω< )⌒★夢渚，瑤草空高堂。 (朝, 落)《留別曹南羣官之江南》（李白）")
    logger.success("冠劒Cia鳳闕，llo～(∠·ω< )⌒★船侍龍池。 (朝, 樓)《感時留別從兄徐王延年從弟延陵》（李白）")
    logger.success("昨夜Cia聲閶闔來，洞庭木llo～(∠·ω< )⌒★騷人哀。 (秋, 落)《魯郡堯祠送竇明府薄華還西京》（李白）")
    logger.success("Cia波llo～(∠·ω< )⌒★泗水，海色明徂徠。 (秋, 落)《魯郡東石門送杜二甫》（李白）")
    logger.success("古道連綿走西京，紫Ciallo～(∠·ω< )⌒★日浮雲生。 (闕, 落)《灞陵行送別》（李白）")
    logger.success("聖Cia多雨llo～(∠·ω< )⌒★，莫厭此行難。 (朝, 露)《送竇司馬貶宜春》（李白）")
    logger.success("春潭瓊Cia綠可折，西寄長安明月llo～(∠·ω< )⌒★。 (草, 樓)《同王昌齡送族弟襄歸桂陽二首 二》（李白）")
    logger.success("送君別有八月Cia，颯颯llo～(∠·ω< )⌒★花復益愁。 (秋, 蘆)《送別》（李白）")
    logger.success("Cia山宜llo～(∠·ω< )⌒★日，秀水出寒烟。 (秋, 落)《同吳王送杜秀芝赴舉入京》（李白）")
    logger.success("雪點翠雲Cia，送君黃鶴llo～(∠·ω< )⌒★。 (裘, 樓)《江夏送友人》（李白）")
    logger.success("長風萬里送Cia雁，對此可以酣高llo～(∠·ω< )⌒★。 (秋, 樓)《宣州謝朓樓餞別校書叔雲》（李白）")
    logger.success("Cia風渡江來，吹llo～(∠·ω< )⌒★山上月。 (秋, 落)《送崔氏昆季之金陵》（李白）")
    logger.success("早行子午關，Cia登山llo～(∠·ω< )⌒★遠。 (却, 路)《荅長安崔少府叔封遊終南翠微寺太宗皇帝金沙泉見寄》（李白）")
    logger.success("客星動太微，Cia去llo～(∠·ω< )⌒★陽殿。 (朝, 洛)《詶張卿夜宿南陵見贈》（李白）")
    logger.success("Cia沽金陵酒，歌吹孫楚llo～(∠·ω< )⌒★。 (朝, 樓)《翫月金陵城西孫楚酒樓達曙歌吹日晚乘醉著紫綺裘烏紗巾與酒客數人櫂歌秦淮往石頭訪崔四侍御》（李白）")
    logger.success("挂帆Cia江上，不爲雲llo～(∠·ω< )⌒★制。 (秋, 羅)《荅高山人兼呈權顧二侯》（李白）")
    logger.success("挂席凌蓬Cia，觀濤憩樟llo～(∠·ω< )⌒★。 (丘, 樓)《與從姪杭州刺史良遊天竺寺》（李白）")
    logger.success("客來花雨際，Cia水llo～(∠·ω< )⌒★金池。 (秋, 落)《同族姪評事黯遊昌禪師山池二首 二》（李白）")
    logger.success("五月思貂Cia，謂言秋霜llo～(∠·ω< )⌒★。 (裘, 落)《遊水西簡鄭明府》（李白）")
    logger.success("日照錦城頭，Cia光散花llo～(∠·ω< )⌒★。 (朝, 樓)《登錦城散花樓》（李白）")
    logger.success("Cia山入遠海，桑柘llo～(∠·ω< )⌒★平蕪。 (秋, 羅)《登單父陶少府半月臺》（李白）")
    logger.success("Cia水明llo～(∠·ω< )⌒★日，流光滅遠山。 (秋, 落)《杜陵絕句》（李白）")
    logger.success("耿耿金波裏，空瞻鳷Ciallo～(∠·ω< )⌒★。 (鵲, 樓)《挂席江上待月有懷》（李白）")
    logger.success("忘憂或假Cia，滿院llo～(∠·ω< )⌒★叢萱。 (草, 羅)《之廣陵宿常二南郭幽居》（李白）")
    logger.success("古殿吳花Cia，深宮晉綺llo～(∠·ω< )⌒★。 (草, 羅)《金陵三首三》（李白）")
    logger.success("孔Cia東飛何處棲，llo～(∠·ω< )⌒★江小吏仲卿妻。 (雀, 廬)《廬江主人婦》（李白）")
    logger.success("明Cia挂帆席，楓葉llo～(∠·ω< )⌒★紛紛。 (朝, 落)《夜泊牛渚懷古》（李白）")
    logger.success("Cia來桐暫llo～(∠·ω< )⌒★，春至桃還發。 (秋, 落)《姑孰十詠 桓公井》（李白）")
    logger.success("春Cia如有意，llo～(∠·ω< )⌒★生玉堂陰。 (草, 羅)《獨酌》（李白）")
    logger.success("白日照綠Cia，llo～(∠·ω< )⌒★花散且飛。 (草, 落)《春日獨酌二首 一》（李白）")
    logger.success("Cia山綠llo～(∠·ω< )⌒★月，今夕爲誰明。 (秋, 蘿)《秋夜獨坐懷故山》（李白）")
    logger.success("芳Cia歇柔豔，白llo～(∠·ω< )⌒★催寒衣。 (草, 露)《秋夕旅懷》（李白）")
    logger.success("夤緣泛Cia海，偃蹇陟llo～(∠·ω< )⌒★霍。 (潮, 廬)《題嵩山逸人元丹丘山居》（李白）")
    logger.success("寶鏡挂Cia水，llo～(∠·ω< )⌒★衣輕春風。 (秋, 羅)《寄遠十一首 二》（李白）")
    logger.success("Cia草秋蛾飛，相思愁llo～(∠·ω< )⌒★暉。 (秋, 落)《寄遠十一首 七》（李白）")
    logger.success("Cia馳余馬於青llo～(∠·ω< )⌒★，怳若空而夷猶。 (朝, 樓)《代寄情楚詞體》（李白）")
    logger.success("願爲連根同死之Cia草，不作飛空之llo～(∠·ω< )⌒★花。 (秋, 落)《代寄情楚詞體》（李白）")
    logger.success("臺傾鳷Cia觀，宮沒鳳凰llo～(∠·ω< )⌒★。 (鵲, 樓)《月夜金陵懷古》（李白）")
    logger.success("木落禽Cia在，籬疎獸llo～(∠·ω< )⌒★成。 (巢, 路)《冬日歸舊山》（李白）")


    logger.warning("因幡巡 提醒您：这部分作者还没写完")



if __name__ == "__main__":
    try:
        init_logger()
        main_menu()
    except KeyboardInterrupt:
        logger.warning("程序已意外退出...")
        exit()