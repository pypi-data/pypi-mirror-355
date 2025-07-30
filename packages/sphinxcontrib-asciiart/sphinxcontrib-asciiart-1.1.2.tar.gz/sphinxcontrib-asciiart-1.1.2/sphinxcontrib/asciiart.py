# -*- coding: utf-8 -*-
import re, os, locale, sys
from os import path
from docutils import nodes, statemachine
from docutils.parsers.rst import Directive, directives
import shutil
from subprocess import Popen, PIPE
from PIL import Image, ImageFont, ImageDraw
try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha

OUTPUT_DEFAULT_FORMATS = dict(html='.html', latex='.pdf', text='.txt')
IMAGE_DEFAULT_FONT = 'SimSun for BBS, SimSun, monospace'
IMAGE_DEFAULT_FONT_SIZE = 14
OWN_OPTION_SPEC = dict({
    #标题
    'caption': str,
    #使用的字体
    'font': str,
    #字体大小
    'fontsize': int,
    #用文件的内容作为输入
    'include': str,
    #一行文字的高度，默认是1.0em, 例如13px, 或者1.1em
    'line-height': str,
    #行间距，两行文字中间额外插入的空白高度, 默认为-1
    'spacing': int,
    #每行最多的字符数，超过就要自动换行，默认为-1, 不自动添加换行
    'textwidth': int,
    #自动换行时，每行前加多少个空格
    'leadingspace': int,
    'suffix': str,
    })

#: the pattern to find ANSI color codes
#COLOR_PATTERN = re.compile('\x1b\\[([^m]+)m')
COLOR_PATTERN = re.compile('(\[([^m]*)m)')

#: map ANSI color codes to class names
CODE_NAME_MAP = {0: ("white",      "bold-white"),
                30: ("black",      "bold-black"),
                31: ("red",        "bold-red"),
                32: ("green",      "bold-green"),
                33: ("yellow",     "bold-yellow"),
                34: ("blue",       "bold-blue"),
                35: ("magenta",    "bold-magenta"),
                36: ("cyan",       "bold-cyan"),
                37: ("white",      "bold-white"),
                40: ("bg_black",   "bg_black"),
                41: ("bg_red",     "bg_red"),
                42: ("bg_green",   "bg_green"),
                43: ("bg_yellow",  "bg_yellow"),
                44: ("bg_blue",    "bg_blue"),
                45: ("bg_magenta", "bg_magenta"),
                46: ("bg_cyan",    "bg_cyan"),
                47: ("bg_white",   "bg_white") }

CODE_CLASS_MAP = {0: ("#b2b2b2", "#ffffff"), #white
        30: ("#111111", "#686868"),          #black
        31: ("#b21717", "#ff5454"),          #red
        32: ("#17b217", "#54ff54"),          #green
        33: ("#b26717", "#ffff54"),          #yellow
        34: ("#1717b2", "#5454ff"),          #blue
        35: ("#b217b2", "#ff54ff"),          #magenta
        36: ("#17b2b2", "#54ffff"),          #cyan
        37: ("#b2b2b2", "#ffffff"),          #white
        40: ("#111111", "#111111"),          #bg_black
        41: ("#b21717", "#b21717"),          #bg_red
        42: ("#17b217", "#17b217"),          #bg_green
        43: ("#b26717", "#b26717"),          #bg_yellow
        44: ("#1717b2", "#1717b2"),          #bg_blue
        45: ("#b217b2", "#b217b2"),          #bg_magenta
        46: ("#17b2b2", "#17b2b2"),          #bg_cyan
        47: ("#b2b2b2", "#b2b2b2"),          #bg_white
        }

class Text2Image(object):
    '''
    PILLOW Image file formats,
    https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
    '''
    def __init__(self, text, **kwargs):
        '''
        '''
        #解析选项: font, fontsize, 注意处理一些非法的字符
        self.font = self._get_image_font(kwargs.get("font",
                                    'NSimSun, simsun, monospace'),
                                    kwargs.get("fontsize", 14))
        if not self.font:
            print("No readable font, return")
            return

        # 解析选项: line-height, spacing, 注意处理一些非法的字符
        self.line_height = self._get_image_line_height(self.font,
                kwargs.get("line-height", "1.0em"))
        self.line_height += kwargs.get("spacing", -1)

        # 初始化
        self.fg_color_index = 0  # 前景色index
        self.bg_color_index = 40  # 背景色index
        self.is_bold = 0          # 前景色是否加粗
        self.cursor = [0, 0]     # 当前的光标位置, for PIL image.

        width = max(self.font.getsize(COLOR_PATTERN.sub('', line))[0] for line in text)
        height = (len(text))*(self.line_height)

        try:
            # call PILLOW to write the text into a image file;
            self.pil_image = Image.new(mode = "RGB", size = (width, height),
                    color = (0x11, 0x11, 0x11))
            self.pil_draw = ImageDraw.Draw(self.pil_image)
        except Exception:
            return

    def _get_image_font (self, fontname, fontsize = 14):
        '''
        解析选项: font, fontsize, 注意处理一些非法的字符
        '''

        p = Popen('fc-list', stdout=PIPE, stdin=PIPE, stderr=PIPE)
        #Get all the font.
        fonts = {}
        stdout, stderr = (p.stdout.read().decode("utf-8"),
                p.stderr.read().decode("utf-8"))
        font0 = stdout.split("\n")[0].split(":")[0]

        #Parse all the fonts
        for l in stdout.split("\n"):
            if l:
                a = l.split(":")
                if a:
                    fonts[a[1].split(".")[0].strip()] = a[0]

        # Some font has alias, also parse them
        for l in stdout.split("\n"):
            if l:
                a = l.split(":")
                if "," in a[1]:
                    for p in a[1].split(","):
                        if p not in fonts.keys():
                            fonts[p.strip()] = a[0]
        #print("fonts: %s" %(fonts))

        for name in fontname.split(","):
            for f in fonts.keys():
                if os.path.basename(name.strip()) == f:
                    # explicit match
                    font = ImageFont.truetype(fonts[f], fontsize, encoding="unic")
                    #print("found1: %s" %(f))
                    return font

        for name in fontname.split(","):
            for f in fonts.keys():
                if os.path.basename(name.strip()) in f:
                    # implicit match
                    font = ImageFont.truetype(fonts[f], fontsize, encoding="unic")
                    #print("found2: %s" %(f))
                    return font

        for f in fonts.keys():
            # return any one.
            font = ImageFont.truetype(fonts[f], fontsize, encoding="unic")
            #print("found3: %s" %(f))
            return font

        return None

    def _get_image_line_height (self, font, high = '1.0em'):
        '''
        解析选项: font, fontsize, 注意处理一些非法的字符
        '''
        try:
            basic_high = font.getsize("_")[1]
        except Exception:
            basic_high = font.getsize("A")[1]+2
        if "px" in high:
            basic_high = high.split('px')[0]
        elif "em" in high:
            basic_high = basic_high*(float(high.split('em')[0]))
        else:
            try:
                basic_high = basic_high + int(high)
            except Exception:
                return int(basic_high)
        return int(basic_high)

    def parse_a_node (self, control_block, color_name = True):
        '''
        Draw a line on the canvas and move the cursor to the start of the next
        line.
        '''
        # 非贪婪模式
        match = re.match(r'[\d;]*?m', control_block, re.M|re.I)
        if match:
            m_index = len(match.group())
            codes = control_block[0:m_index-1].split(";")
            for code in codes:
                try:
                    n = int(code)
                except Exception:
                    n = 0

                if n >= 30 and n <= 37:
                    self.fg_color_index = n
                elif n >= 40 and n <= 47:
                    self.bg_color_index = n
                elif n == 1:
                    self.is_bold = 1
                elif n == 0:
                    self.is_bold = 0
                    self.fg_color_index = 0
                    self.bg_color_index = 40
        else:
            m_index = 0

        if color_name:
            return (CODE_NAME_MAP[self.fg_color_index][self.is_bold],
                    CODE_NAME_MAP[self.bg_color_index][0],
                    control_block[m_index:])
        else:
            return (CODE_CLASS_MAP[self.fg_color_index][self.is_bold],
                    CODE_CLASS_MAP[self.bg_color_index][0],
                    control_block[m_index:])

    def draw_string(self, fg_color, bg_color, string):
        '''
        Draw a string on the canvas and move the cursor to the end.
        '''
        text_size = self.pil_draw.textsize(string, font = self.font)
        self.pil_draw.rectangle([self.cursor[0],
            self.cursor[1],
            self.cursor[0] + text_size[0],
            self.cursor[1] + self.line_height],
            fill=bg_color)
        # 当行距不足时，会覆盖上一行几个像素的数据。将文本往上画一行，这样当
        # spacing=-2 时上下各覆盖一个像素而不是覆盖下面的两个像素
        self.pil_draw.text((self.cursor[0], self.cursor[1]-1),
                string, font = self.font, fill = fg_color)
        self.cursor[0] += text_size[0]

    def asciiart_literal_block_to_html (self, app, block):
        '''
        Convert the literal block to html format. html mode is only supported
        by html output
        '''
        if app.builder.name == 'text':
            return pil.asciiart_literal_block_to_text(app, block)
        elif app.builder.name != 'html':
            return pil.asciiart_literal_block_to_image(app, block, "png")

        # create the "super" node, which contains to while block and all it
        # sub nodes, and replace the old block with it
        literal_node = nodes.literal_block()
        literal_node['classes'].append('ansi-block')
        block.replace_self(literal_node)

        # devide the txt to nodes by '\x1B['. txt[i] is color + text;
        txt = '\n'.join(block.asciiart['text']).split('\x1B[')
        for i in range(0, len(txt)):
            (fg_color, bg_color, text) = self.parse_a_node(txt[i], True)
            # Add the color/text into the list;
            code_node = nodes.inline()
            code_node['classes'].append('ansi-%s' % fg_color)
            code_node['classes'].append('ansi-%s' % bg_color)
            code_node.append(nodes.Text(text))
            literal_node.append(code_node) # and add the nodes to the block
        print("rending asciiart literal block in html format")

    def asciiart_literal_block_to_text (self, app, block):
        '''
        Strip all color codes and save to text file.
        '''
        #content = COLOR_PATTERN.sub('', block.rawsource)
        content = COLOR_PATTERN.sub('', '\n'.join(block.asciiart['text']))
        literal_node = nodes.literal_block(content, content)
        block.replace_self(literal_node)
        print("rending asciiart literal block in plain text format")

    def asciiart_literal_block_to_image (self, app, fig, suffix):
        '''
        Convert the literal block to image for including in the target.
        '''
        #hashkey = sha('\n'.join(fig.asciiart['text']).encode('utf-8')).hexdigest()
        hashkey = str(fig.asciiart['text']) + str(fig.asciiart['options']) +\
                str(app.builder.config.ascii_art_image_fontsize) +\
                str(app.builder.config.ascii_art_image_font)
        hashkey = sha(hashkey.encode('utf-8')).hexdigest()
        options = fig.asciiart['options']

        outfname = 'asciiart-%s.%s' %(hashkey, suffix.strip("."))
        out = dict(outrelfn=None,outfullfn=None,outreference=None)
        out["outrelfn"] = path.join(app.builder.imagedir, outfname)
        out["outfullfn"] = path.join(app.builder.outdir, app.builder.imagedir, outfname)

        #if ((not fig.get('height', None))
        #        and (not fig.get('width', None))
        #        and (not fig.get('scale', None))):
        #    # Keep the original height x width to avoid to magnify in pdf
        #    fig['height'] = "%d" %(self.pil_image.height)
        #if path.isfile(out["outfullfn"]):
        #    # 如果图片已经存在就不用再生成一次.
        #    fig['uri'] = out["outrelfn"]
        #    return
        #out["outreference"] = posixpath.join(rel_imgpath, infname)

        for line in fig.asciiart['text']:
            #print(font.getsize(COLOR_PATTERN.sub('', line)))
            txt = line.split('\x1B[')
            for i in range(0, len(txt)):
                (fg_color, bg_color, t) = self.parse_a_node(txt[i], False)
                self.draw_string(fg_color, bg_color, t)
            self.cursor[0] = 0
            self.cursor[1] += self.line_height
        imagedir = path.join(app.builder.outdir, app.builder.imagedir)

        if not os.path.exists(imagedir):
            os.mkdir(imagedir)
        self.pil_image.save(out["outfullfn"])
        print("asciiart literal block --> %s" %(outfname))
        #print("fig1: %s" %(fig))
        caption_node = nodes.caption("", options.get("caption", "test"))
        for c in fig.traverse(condition=nodes.caption):
            #docutils.nodes.Element,
            #https://tristanlatr.github.io/apidocs/docutils/docutils.nodes.Element.html
            c.replace_self(caption_node)
        fig['ids'] = ["asciiart"]
        #uri
        for img in fig.traverse(condition=nodes.image):
            img['uri'] = out["outrelfn"]
        #print("%s(), fig: %s" %(sys._getframe().f_code.co_name, fig))

def render_asciiart_images(app, doctree):
    for img in doctree.traverse(nodes.image):
        #print("img1: %s" %(img))
        if not hasattr(img, 'asciiart'):
            continue

        try:
            format_map = OUTPUT_DEFAULT_FORMATS.copy()
            format_map.update(app.builder.config.ascii_art_output_format)
            output_format = format_map.get(app.builder.name, "png")
        except:
            output_format = "png"

        global_option = {}
        if not img.asciiart['options'].get('font', None):
            global_option["font"] = app.builder.config.ascii_art_image_font \
                    and app.builder.config.ascii_art_image_font \
                    or IMAGE_DEFAULT_FONT
        if not img.asciiart['options'].get('fontsize', None):
            global_option["fontsize"] = app.builder.config.ascii_art_image_fontsize \
                    and app.builder.config.ascii_art_image_fontsize \
                    or IMAGE_DEFAULT_FONT_SIZE

        pil = Text2Image(img.asciiart['text'], **img.asciiart['options'], **global_option)
        if hasattr(img, 'asciiart'):
            if output_format.lower() in [".html", "html"]:
                pil.asciiart_literal_block_to_html(app, img)
            elif output_format.lower() in [".txt", "txt"]:
                pil.asciiart_literal_block_to_text(app, img)
            elif output_format.lower() in [ "bmp", ".bmp", "dib", ".dib",
                    "eps", ".eps", "gif", ".gif", "icns", ".icns", "ico",
                    ".ico", "im",  ".im", "jpg", ".jpg", "jpeg", ".jpeg",
                    "msp", ".msp", "pcx", ".pcx", "png", ".png", "ppm", ".ppm",
                    "sgi", ".sgi", "spider", ".spide", "tga", ".tga", "tiff",
                    ".tiff", "webp", ".webp", "xbm", ".xbm", "palm", ".palm",
                    "pdf", ".pdf", "xv",  ".xv", "bufr", ".bufr", "fits", ".fits",
                    "grib", ".grib", "hdf5", ".hdf5", "mpeg", ".mpeg"]:
                pil.asciiart_literal_block_to_image(app, img, output_format)
            else:
                print("Not supported suffix: %s, convert it to plain text"
                        %(output_format))
                pil.asciiart_literal_block_to_text(app, img)
    for fig in doctree.traverse(nodes.figure):
        #print("img2: %s" %(fig))
        if not hasattr(fig, 'asciiart'):
            continue

        try:
            format_map = OUTPUT_DEFAULT_FORMATS.copy()
            format_map.update(app.builder.config.ascii_art_output_format)
            output_format = format_map.get(app.builder.name, "png")
        except:
            output_format = "png"

        global_option = {}
        if not fig.asciiart['options'].get('font', None):
            global_option["font"] = app.builder.config.ascii_art_image_font \
                    and app.builder.config.ascii_art_image_font \
                    or IMAGE_DEFAULT_FONT
        if not fig.asciiart['options'].get('fontsize', None):
            global_option["fontsize"] = app.builder.config.ascii_art_image_fontsize \
                    and app.builder.config.ascii_art_image_fontsize \
                    or IMAGE_DEFAULT_FONT_SIZE

        pil = Text2Image(fig.asciiart['text'], **fig.asciiart['options'], **global_option)
        if hasattr(fig, 'asciiart'):
            if output_format.lower() in [".html", "html"]:
                pil.asciiart_literal_block_to_html(app, fig)
            elif output_format.lower() in [".txt", "txt"]:
                pil.asciiart_literal_block_to_text(app, fig)
            elif output_format.lower() in [ "bmp", ".bmp", "dib", ".dib",
                    "eps", ".eps", "gif", ".gif", "icns", ".icns", "ico",
                    ".ico", "im",  ".im", "jpg", ".jpg", "jpeg", ".jpeg",
                    "msp", ".msp", "pcx", ".pcx", "png", ".png", "ppm", ".ppm",
                    "sgi", ".sgi", "spider", ".spide", "tga", ".tga", "tiff",
                    ".tiff", "webp", ".webp", "xbm", ".xbm", "palm", ".palm",
                    "pdf", ".pdf", "xv",  ".xv", "bufr", ".bufr", "fits", ".fits",
                    "grib", ".grib", "hdf5", ".hdf5", "mpeg", ".mpeg"]:
                pil.asciiart_literal_block_to_image(app, fig, output_format)
            else:
                print("Not supported suffix: %s, convert it to plain text" %(output_format))
                pil.asciiart_literal_block_to_text(app, fig)

class AsciiArtDirective(directives.images.Figure):
    """
    扫描文档时如果找到..assciiart:: 命令后建议一个空的figure对象，并且将
    .. asciiart:: 的内容保存在figure对象上。

    https://learn-rst.readthedocs.io/zh_CN/latest/reST-%E6%89%A9%E5%B1%95/reST-%E8%87%AA%E5%AE%9A%E4%B9%89%E6%89%A9%E5%B1%95.html
    The asciiart directive parse the color in the literal block and render
    them:

    .. asciiart:: 

        ascii art block.

    """
    # this enables content in the directive
    has_content = True
    required_arguments = 0
    option_spec = directives.images.Figure.option_spec.copy()
    option_spec.update(OWN_OPTION_SPEC)
    def run(self):
        '''
        This method must process the directive arguments, options and content,
        and return a list of Docutils/Sphinx nodes that will be inserted into
        the document tree at the point where the directive was encountered.
        '''
        self.arguments = ['']
        asciiart_options = dict([(k,v) for k,v in self.options.items() 
                                        if k in OWN_OPTION_SPEC])

        #Use include as self.content, docutils.statemachine.StringList
        if asciiart_options.get("include", None):
            print("include: %s." %(asciiart_options.get("include", None)))
            with open(asciiart_options["include"], 'r') as f:
                content = [line.strip() for line in f.readlines()]
                self.content = statemachine.StringList(content)

        #将字符按textwidth自动换行，注意控制字符不占位置
        if asciiart_options.get("textwidth", 0) > 0:
            textwidth = asciiart_options["textwidth"]
            leadingspace = asciiart_options.get("leadingspace", 0)
            print("textwidth(%d) > 0, will reformat the content." %(textwidth))
            text = []
            for line in self.content:
                if len(COLOR_PATTERN.sub('', line)) > textwidth:
                    counter = 0
                    new = ""
                    for i in line:
                        new += i
                        #new += (i == '_') and '\_' or i
                        if (i not in '(\[([^m]*)m)'):
                            counter += 1
                            if (counter >= textwidth) and i.isspace():
                                text.append(new + "\\")
                                counter = leadingspace
                                #new = "." + " "*counter
                                new = " "*counter
                    if counter != 0:
                        text.append(new)
                else:
                    text.append(line)
            self.content = statemachine.StringList(text)

        # 因为在这里读不到app.builder.config.ascii_art_output_format 的值，
        # 所以我们把所有的节点初始化为Figure 节点，以后需要的时候再替换成
        # literal_block
        #print("content type: %s." %(type(self.content)))
        #print("content: %s." %(self.content))
        (node,) = directives.images.Figure.run(self)
        node.asciiart = dict(text=self.content, options=asciiart_options,
                suffix="asciiart", directive="asciiart")
        return [node]

def add_stylesheet(app):
    app.add_css_file('asciiart.css')

def copy_stylesheet(app, exception):
    # Copy the style sheet to the dest _static directory
    if app.builder.name != 'html' or exception:
        return
    dest = path.join(app.builder.outdir, '_static', 'asciiart.css')
    source = path.join(path.dirname(__file__), 'asciiart.css')
    try:
        shutil.copy(source, dest)
    except:
        print('Fail to copy %s to %s.' %(source, dest))


def setup(app):
    app.add_directive('asciiart', AsciiArtDirective)
    #app.connect('doctree-resolved', AsciiArtParser())
    app.connect('doctree-read', render_asciiart_images)
    app.connect('builder-inited', add_stylesheet)
    app.connect('build-finished', copy_stylesheet)
    app.add_config_value('ascii_art_output_format', OUTPUT_DEFAULT_FORMATS, 'html')
    app.add_config_value('ascii_art_image_font', IMAGE_DEFAULT_FONT, 'html')
    app.add_config_value('ascii_art_image_fontsize', IMAGE_DEFAULT_FONT_SIZE, 'html')
