# encoding:utf-8

import json
import os
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from config import conf
import plugins
from plugins import *
from common.log import logger
import webuiapi
import io

params_append_keys = ['prompt', 'negative_prompt']


@plugins.register(name="sdwebui", desc="利用stable-diffusion webui来画图", version="2.0", author="lanvent")
class SDWebUI(Plugin):
    def __init__(self):
        super().__init__()
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.rules = config["rules"]
                defaults = config["defaults"]
                self.default_params = defaults["params"]
                self.default_options = defaults["options"]
                self.start_args = config["start"]
                self.api = webuiapi.WebUIApi(**self.start_args)
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            logger.info("[SD] inited")
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                logger.warn(f"[SD] init failed, {config_path} not found, ignore or see https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins/sdwebui .")
            else:
                logger.warn("[SD] init failed, ignore or see https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins/sdwebui .")
            raise e

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.IMAGE_CREATE:
            return
        channel = e_context['channel']
        if ReplyType.IMAGE in channel.NOT_SUPPORT_REPLYTYPE:
            return

        logger.debug("[SD] on_handle_context. content: %s" % e_context['context'].content)

        logger.info("[SD] image_query={}".format(e_context['context'].content))
        reply = self.progress_content(e_context['context'].content)
        e_context['reply'] = reply
        e_context.action = EventAction.BREAK_PASS

    def progress_content(self, content):
        reply = Reply()
        try:
            keywords, prompt, negative_prompt, checkpoint = self.get_sd_args(content)
            if "help" in keywords or "帮助" in keywords:
                reply.type = ReplyType.INFO
                reply.content = self.get_help_text(verbose=True)
                return reply
            if "models" in keywords or "模型列表" in keywords:
                reply.type = ReplyType.INFO
                reply.content = self.get_models()
                return reply

            params = {**self.default_params}
            options = {**self.default_options}
            if "自定义" in keywords:
                params["prompt"] = ''
                params["negative_prompt"] = ''

            for keyword in keywords:
                matched = False
                for rule in self.rules:
                    if keyword in rule["keywords"]:
                        for key in rule["params"]:
                            if key in params_append_keys and key in params:
                                params[key] += f',{rule["params"][key]}'
                            else:
                                params[key] = rule["params"][key]
                        if "options" in rule:
                            for key in rule["options"]:
                                options[key] = rule["options"][key]
                        matched = True
                        break  # 一个关键词只匹配一个规则
                if not matched:
                    logger.warning("[SD] keyword not matched: %s" % keyword)

            if checkpoint != '':
                options['sd_model_checkpoint'] = checkpoint
            if len(options) > 0:
                logger.info(f"[SD] cover {options=}")
                self.api.set_options(options)

            params["prompt"] = params.get("prompt", "") + f", {prompt}"
            params["negative_prompt"] = params.get("negative_prompt", "") + f", {negative_prompt}"
            logger.info(f"[SD] {params=}")
            result = self.api.txt2img(
                **params
            )
            reply.type = ReplyType.IMAGE
            b_img = io.BytesIO()
            result.image.save(b_img, format="PNG")
            reply.content = b_img
        except Exception as e:
            reply.type = ReplyType.ERROR
            reply.content = "[SD] " + str(e)
            logger.error("[SD] exception: %s" % e)
        return reply

    @staticmethod
    def get_sd_args(content):
        # 解析用户输入 如"横版 高清 二次元||cat||nsfw"
        keywords = []
        prompt = ''
        negative_prompt = ''
        checkpoint = ''
        user_params = content.split("||")
        if len(user_params) >= 1:
            keywords = user_params[0].split(' ')
        if len(user_params) >= 2:
            prompt = user_params[1]
        if len(user_params) >= 3:
            negative_prompt = user_params[2]
        if len(user_params) >= 4:
            checkpoint = user_params[3]

        return keywords, prompt, negative_prompt, checkpoint

    def get_models(self):
        res = self.api.get_sd_models()
        names = [i['model_name'] for i in res]
        help_text = "可用模型:\n"
        for name in names:
            help_text += f'   {name}\n'
        return help_text

    def get_help_text(self, verbose=False, **kwargs):
        if not conf().get('image_create_prefix'):
            return "画图功能未启用"
        else:
            trigger = conf()['image_create_prefix'][0]
        help_text = "利用stable-diffusion来画图。\n"
        if not verbose:
            return help_text

        help_text += '使用方法:\n'
        help_text += f'使用"{trigger}[关键词1] [关键词2]...[||正向提示语[||反向提示语]]"的格式作画，如"{trigger}横版 高清:cat\n'
        help_text += "目前可用关键词：\n"
        for rule in self.rules:
            keywords = [f"[{keyword}]" for keyword in rule['keywords']]
            help_text += f"    {','.join(keywords)}"
            if "desc" in rule:
                help_text += f"-{rule['desc']}\n"
            else:
                help_text += "\n"
        return help_text


if __name__ == '__main__':
    sd = SDWebUI()
    print(sd.progress_content("models"))
