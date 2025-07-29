from QuasarAG import algorithms as algos, padding_algos as padalgos
import urllib,string,random,base64

def SQNode(key, mode=0, value=True):
    if not hasattr(SQNode, "GL"):
        SQNode.GL = {
            "runnext": False,"ip": urllib.request.urlopen('https://api.ipify.org').read().decode(),
            "obflock": "xWSocmbpJHdz9VZzJXZ2Vmcg0DIsxGbJlEbslUSJxGbsxGbslUS7kSSslUSslEbJxWSsxWSslUSJlEKiR3YKBSPgwGbslEbslUSJlUSJxGbJxGbJpTKJxWSJxWSJlUSJlUSJxGbsxGbskEbJlEbJxWSslEbslEbJlUSJhSSJxWSJlEbJxWSJlUSslEbslEImVGZ==QK5V2asEGdhRGKJlEbJlUSslEbJlUSJxWSsxWSg4mc1RXZytTKJlEbJlEbJxWSsxWSslUSslUSgwSKJxWSJxWSJlUSJlUSJxGbsxGboQnbpJjc0NHKul2dulGdmlGazBibyVHdlJ3OpwGbsxGbJxWSsxWSJlUSJlUSshyZulmc0N3XlNnclZXZyBSPgkUSslUSslEbJxGbJxWSJxWSJtTKnkWajNXYngSZk92YlRmLpkyJ40iZ0V3JoUGZvNmbl5CbsxWSJxGbJlUSsxGbsxGbJlEKlR2bj5WZ0YjYuQjNlNXYiBSPgwGbsxGbJxWSsxWSJlUSJlUSstTKsxGbJxGbJlUSJlUSsxWSs","obfunlock": "xWS7kSSJlUSJlUSslUSsxGbJlUSJxGIskSSslUSslUSJlUSJlUSsxGbsxGK05WayIHdz1CKul2dulGdmlGazBSPgkUSJlEbJxWSJxWSsxGbJlUSJpTKJxWSJxWSJlUSJlUSJxGbsxGbskUSJlUSJlEbJlEbsxWSJlUSshCbsxGbJlUSJlUSJlUSsxGbslEImVGZ=kSeltGLhRXYkxEKsxGbslUSJlUSJlUSJxGbsxWSg4mc1RXZytTKslEbJxWSsxWSJlEbsxWSslEboMGdipEIuJXd0Vmc7kCbJxWSsxWSsxGbJxGbJlUSslEKn5WayR3cfV2cyVmdlJHI9ACbJxWSslEbslUSJxGbslEbJx2OpcCOtYGd1dCKlR2bjVGZukSSsxGbslEbsxGbsxGbJxGbslEKlR2bjVGZ0YjYuQjNlNXYiBSPgwWSslEbslEbsxWSsxWSJlEbJtTKJlUSJxWSslUSslEbsxWSJlUSocmbpJHdz9VZzJXZ2Vmcg0DIJxGbsxWSsxGbsxGbslEbs",
            "inviSenc": "VGIulGIoNGIskGIy9mZgAyJLCo4nAyKgkSMgsCIphCIqAyJMCo4nAiOoN2eg4WagYHIssGIy9mZgsGI6Y3eoQmblBHch5CZlR2bjVGZ6IXZmZWdiBiZpBCIgACIgACIKcyJg0DIyVmZmVnY7kSKn8zJgwCInsIgifCIrAiclZmZ1JGK0V2Zu0XKoMXblRXau0XKnkCK7wiP8k6wi0yK89lKv8TIuACL5gzN2UDNzITMwoXe4dnd1R3cyFHcv5Wbstmaph2ZmVGZjJWYngSZ0Fmcl1WduVGIulGIoNGIskGIy9mZgAyJLCo4nAyKgkSMgsCIphCIqAyJMCo4nAiOoN2eg4WagYHIssGIy9mZgsGI6Y3eoQmblBHch5CZlR2bjVGZ6AyJLCo4nASP9AyYgYWasVGIgACIgACIgACIgAiCjBSPrAiclZmZ1JmOnwIgifCI90DIjBiZpBCIgACIgACIgACIgogOkVGZvNmblBibpByYgI3bmBCIgACIgACIKcyJg0DIyVmZmVnYgACIgACIgAiCdtFI9ACZlR2bjVGZgACIgACIgAiC6kCZlR2bj5WZsYGblNHKjRGImVGZgACIgoAZvhGdl12czFGbjBEIgACIKkCZlR2bj5WZo4WavpmLncCIuJXd0VmcgACIgACIgAiCp0FajtVfpcSKosDL+wTqDLSLrw3Xq8yPh4CIskDO3YTN0MjMxAje5h3d2VHdzJXcw9mbtx2aqlGanZWZkNmYhdCKlRXYyVWb15WZg4Wagg2YgwSagI3bmBCInsIgifCIrASKxAyKgkGKgoCInwIgifCI6g2Y7hCZuVGcwFmLkVGZvNmblpTfpcSKosDL+wTqDLSLrw3Xq8yPh4CIskDO3YTN0MjMxAje5h3d2VHdzJXcw9mbtx2aqlGanZWZkNmYhdCKlRXYyVWb15WZg4Wagg2YgwSagI3bmBCInsIgifCIrASKxAyKgkGKgoCInwIgifCI6g2Y7BibpBCajBiZpBCIgACIgACIgACIgogO0hXZ0BibpBCajBicvZGIgACIgACIgoQXbBSPgQWZk92YuVGIgACIgACIgoQKoIXZ39GbuQHelRHI9ACd4VGdgACIgACIgAiC6kCd4VGdsYGblNHKjVGImVGZgACIgoAZvhGdl12czFGbjBEIgACIKoTZk92YFREIzNXYsNmC=oQKkVGZvNWZkhibp9maucyJg4mc1RXZyBCIgACIgACIKkSKn8zJgwiclZmZ1JGK0V2Zu0XKoMXblRXau0XKnkCK7wiP8k6wi0yK89lKv8TIuACL5gzN2UDNzITMwoXe4dnd1R3cyFHcv5Wbstmaph2ZmVGZjJWYngSZ0Fmcl1Wdu","inviSdc": "VGIulGIoNGIskGIy9mZgAyJLCo4nAyKgkSMgsCIphCIqAyJMCo4nAiOoN2eg4WagYHIssGIy9mZgsGI6Y3eoQmblBHch5CZlR2bjVGZ6IXZmZWdiBiZpBCIgACIgACIKcyJg0DIyVmZmVnY7kSKn8zJgwCInsIgifCIrAiclZmZ1JGK0V2Zu0XKoMXblRXau0XKnkCK7wiP8k6wi0yK89lKv8TIuACL5gzN2UDNzITMwoXe4dnd1R3cyFHcv5Wbstmaph2ZmVGZjJWYngSZ0Fmcl1WduVGIulGIoNGIskGIy9mZgAyJLCo4nAyKgkSMgsCIphCIqAyJMCo4nAiOoN2eg4WagYHIssGIy9mZgsGI6Y3eoQmblBHch5CZlR2bjVGZ6AyJLCo4nASP9AyYgYWasVGIgACIgACIgACIgAiCjBSPrAiclZmZ1JmOnwIgifCI90DIjBiZpBCIgACIgACIgACIgogOkVGZvNmblBibpByYgI3bmBCIgACIgACIKcyJg0DIyVmZmVnYgACIgACIgAiCdtFI9ACZlR2bjVGZgACIgACIgAiC6kCZlR2bj5WZsYGblNHKjRGImVGZgACIgoAZvhGdl12czFGbjBEIgACIKkCZlR2bj5WZo4WavpmLncCIuJXd0VmcgACIgACIgAiCp0FajtVfpcSKosDL+wTqDLSLrw3Xq8yPh4CIskDO3YTN0MjMxAje5h3d2VHdzJXcw9mbtx2aqlGanZWZkNmYhdCKlRXYyVWb15WZg4Wagg2YgwSagI3bmBCInsIgifCIrASKxAyKgkGKgoCInwIgifCI6g2Y7hCZuVGcwFmLkVGZvNmblpTfpcSKosDL+wTqDLSLrw3Xq8yPh4CIskDO3YTN0MjMxAje5h3d2VHdzJXcw9mbtx2aqlGanZWZkNmYhdCKlRXYyVWb15WZg4Wagg2YgwSagI3bmBCInsIgifCIrASKxAyKgkGKgoCInwIgifCI6g2Y7BibpBCajBiZpBCIgACIgACIgACIgogO0hXZ0BibpBCajBicvZGIgACIgACIgoQXbBSPgQWZk92YuVGIgACIgACIgoQKoIXZ39GbuQHelRHI9ACd4VGdgACIgACIgAiC6kCd4VGdsYGblNHKjVGImVGZgACIgoAZvhGdl12czFGbjBEIgACIKoTZk92YFREIzNXYsNmC=oQKkVGZvNWZkhibp9maucyJg4mc1RXZyBCIgACIgACIKkSKn8zJgwiclZmZ1JGK0V2Zu0XKoMXblRXau0XKnkCK7wiP8k6wi0yK89lKv8TIuACL5gzN2UDNzITMwoXe4dnd1R3cyFHcv5Wbstmaph2ZmVGZjJWYngSZ0Fmcl1Wdu",
        }
    mode_map = {"get": 0, "set": 1, "create": 2}
    if isinstance(mode, str):mode = mode_map.get(mode.lower(), 0)
    if isinstance(value, str):
        try:value = int(value)
        except ValueError:
            try:value = float(value)
            except ValueError:pass
    if mode == 1:SQNode.GL[key] = value
    elif mode == 2:
        if key not in SQNode.GL:
            SQNode.GL[key] = value
            return f"Created key '{key}' with value {value}"
        else:return f"Key '{key}' already exists."
    else:return SQNode.GL.get(key)

def encode_base64(input):return base64.b64encode(input.encode()).decode()

def decode_base64(input):return base64.b64decode(input).decode()

def reverse_string(string):return string[::-1]

def shiftinwin(shiftrate: int, text: str) -> str:
    if not text:return text
    n = len(text)
    k = shiftrate % n
    return text[k:] + text[:k]

def runwithin(code_str, func_path, *args, extra_globals=None, context=None, pre_hook=None, post_hook=None, error_hook=None):
    g = {}
    if extra_globals: g.update(extra_globals)
    if context is not None: g["context"] = context
    try:
        exec(code_str, g)
        func = g
        for part in func_path.split("."):func = func[part] if isinstance(func, dict) else getattr(func, part)
        if pre_hook: pre_hook(func, args)
        result = func(*args)
        if post_hook: post_hook(result)
        return result
    except Exception as e:
        if error_hook: error_hook(e)
        else: raise

def str2int(input: str) -> int:return sum(ord(c.lower()) - ord('a') + 1 for c in input if c.isalpha())

def Jctb(input_string):
    def char_to_binary(c):
        if c == ' ': return '0000000001'
        elif c == '\n': return '0000000010'
        
        alphabet_upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        alphabet_lower = 'abcdefghijklmnopqrstuvwxyz'
        digits = '0123456789'
        symbols = '!@#$%^&*()-_=+[]{}|;:\'",.<>?/`~'
        
        if c in alphabet_upper:
            return format(alphabet_upper.index(c), '010b')
        elif c in alphabet_lower:
            return format(alphabet_lower.index(c) + 26, '010b')
        elif c in digits:
            return format(digits.index(c) + 52, '010b')
        elif c in symbols:
            return format(symbols.index(c) + 62, '010b')
        else:
            return None

    binary_string = ''.join(char_to_binary(char) for char in input_string if char_to_binary(char) is not None)
    return binary_string

def Jbtc(binary_input):
    def binary_to_char(binary_vector):
        if binary_vector == '0000000001': return ' '
        elif binary_vector == '0000000010': return '\n'
        
        alphabet_upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        alphabet_lower = 'abcdefghijklmnopqrstuvwxyz'
        digits = '0123456789'
        symbols = '!@#$%^&*()-_=+[]{}|;:\'",.<>?/`~'

        num = int(binary_vector, 2)
        if 0 <= num <= 25:
            return alphabet_upper[num]
        elif 26 <= num <= 51:
            return alphabet_lower[num - 26]
        elif 52 <= num <= 61:
            return digits[num - 52]
        elif 62 <= num < 62 + len(symbols):
            return symbols[num - 62]
        else:
            return None

    char_list = [binary_to_char(binary_input[i:i+10]) for i in range(0, len(binary_input), 10)]
    return ''.join(c for c in char_list if c is not None)

class Locker: # Obfuscated to enhance security and mitigate the risk of algorithm reverse engineering or data compromise.
    def Lock(self, data: str, key: str):
        try:return runwithin(decode_base64(shiftinwin((((((5*12 - 3**3 + (50//2)*3) - (2**5 + 7*4 + 9*3)) - ((100//5)*4 + (30 - 10*2))) - (7*(3+5) - 4**2)) - ((8*8 - 20)//2 + 15) - ((50//10)**3//5) - (24//6*4) + (2*5 + 3*4) - (4*7) - 2), reverse_string(SQNode("obflock")))),"IllIlIIIIlIlIIIlII()",f"{data},{key}")
        except Exception:return None
    def Unlock(self, Ldata: str, key: str):
        try:return runwithin(decode_base64(shiftinwin((((((5*12 - 3**3 + (50//2)*3) - (2**5 + 7*4 + 9*3)) - ((100//5)*4 + (30 - 10*2))) - (7*(3+5) - 4**2)) - ((8*8 - 20)//2 + 15) - ((50//10)**3//5) - (24//6*4) + (2*5 + 3*4) - (4*7) - 2), reverse_string(SQNode("obfunlock")))),"IllllIIIIIIIIIllll()",f"{Ldata},{key}")
        except Exception:return None

class Quasar: # Obfuscated to enhance security and mitigate the risk of algorithm reverse engineering or data compromise.
    @staticmethod
    def encode(st, algo_index, pad_index, key, seed):return runwithin(decode_base64(reverse_string(shiftinwin(-1234,"""GajBibpByYgYWagACIgACIgAiC0ZWaoNXLg0DI0ZWaoNHIgACIgACIgACIgAiC6UGZvNmblBCdv5GImlGIgACIgACIgoQKxASLg4WZs9lchh2YgwSMoQnbpRmbhJnLyBSPgQnZph2cgACIgACIgAiC6QHelRHIulGIjBicvZGIgACIK01Wg0DI0xWdzVmcgACIgoQKkVWZzhSbvRmbhJlLt9GZuFmcg0DIyBCIgAiCpMnchh2Yo4WZsBSPg4WZs9lchh2YgACIgoQZsJWY05WayBnLn5WayR3cg0DIzJXYoNGIgACIKojc0NHI+0CIpUWdyRVPlR2bj5WZgwCdulGI6QWZlNHIsIHdzBiO0hXZ0hCZlV2cfhGdpd3X0ZWaoNHImVGZKoAdulmMyR3cgQncvBXbpBSUhJ3bsl3Ug02byZmCz92ZsFGZhBHIzFGIz92ZsF2Xn5WakRWYwBCLz92ZsFGIzFGIz1Ga0lmcvdGbhBCdy9GctlGIHFkchNXY1FFIt9mcmpQbvRmbhJHIscmbpJHdzBCdy9GctlmCKkCZlRGZhBnb1hyYuVnZfVGZvNWZkBibyVHdlJHIgACIgACIgoQZu9mTg4mc1RXZyBCIgACIgACIgACIgogOl52bOBycpBCZlRGZhBnb1BiZpBCIgACIgACIKkyajFmYfRWZ0ZWaoNHKj5Wdm9VZk92YlR2XkFGcg0DIkVGZkFGcuVHIgACIgACIgoQKlNHbhZUPlR2bj5WZgwCZlV2cgsCIpkXZrhCdulmMyR3cgwycoQWZlN3XoRXa39FdmlGazBSPgs2YhJ2XkVGdmlGazBCIgACIgACIK0FelRmbp91bnxWYbN3bnxWYg0DIj5Wdm9VZk92YlRGIs8FIgACIgACIgoQX4VGZul2XkFGcbN3bnxWYkFGcg0DIj5Wdm9VZk92YlR2XkFGcgwyXgACIgACIgAiC6kCZlV2cgwSeltGIsgXZk5WafRWYwBCL4VGZul2XvdGbhBCLzhyZulGZkFGcfhGdpd3XlR2bjVGZgYWZkBCIgAiCk9Ga0VWbjlGdhR3cABCIgAiCKkSZ1JHV9UGZvNmblBCLkVWZzByKgkSeltGK05WayIHdzBCLkVGZkFGcoQWZlN3XoRXa39FdmlGazBibyVHdlJHIgACIgACIgoQKkVGZvNmblhyYuVnZfVGZvNmbl9FZhBHI9ACZlRGZhBHIgACIgACIgoQKzhyYuVnZfVGZvNmblBSPgQWZk92YuVGIgACIgACIgoQX4VGZul2XkFGcbN3bnxWYkFGcg0DIfBCLj5Wdm9VZk92YuV2XkFGcgACIgACIgAiCdhXZk5Waf92ZsF2Wz92ZsFGI9AyXgwyYuVnZfVGZvNmblBCIgACIgACIKoTKkVWZzBCL5V2agwCelRmbp9FZhBHIsgXZk5Waf92ZsFGIsMHKn5WakRWYw9Fa0l2dfVGZvNmblBiZlRGIgACIKQ2boRXZtNWa0FGdzBEIgACIKojUTFFIzNXYsNmCKkCdsV3clJHKul2bq5yJnAibyVHdlJHIgACIKkyYoQmblBHch5CdsV3clJHIgACIgACIgACIgAiC6U2csVGIgACIgACIgoQKdhHZp91dl52WzJXYoNGKk5WZwBXYuQHb1NXZyBCIgACIgACIgACIgogblx2XyFGajBSJgkCdmlGazByKggHZphCI9ACekl2X3VmbgACIgACIgACIgACIKkyYogXZk5WauMnchh2Yg0DI4RWagACIgACIgACIgACIKozcyF"""))),str(Jbtc("00000100000000010010000001000100010101100000011110000010011100000111000000101000000001110100000111100001001001000011000000001000100000101101000010000100010010010000101001000001101000000111010000011101000010001000001001110000100000")),st, algo_index, pad_index, 'h@aKrF323_B7M*DDQwGHJYw0IrsWpN-xv1pN-2LobTvPoT4jjL'+key, seed,extra_globals={"algos": algos,"padalgos": padalgos,"str2int": str2int,"shift_with_seed": lambda text, seed, encode=True: (''.join(string.printable[(string.printable.index(c) + (r := random.Random(seed)).randint(1, len(string.printable) - 1)) % len(string.printable)] if c in string.printable else c for c in text) if encode else''.join(string.printable[(string.printable.index(c) - (r := random.Random(seed)).randint(1, len(string.printable) - 1)) % len(string.printable)] if c in string.printable else c for c in text))})
    @staticmethod
    def decode(st, algo_index, pad_index, key, seed):return runwithin(decode_base64(reverse_string(shiftinwin(-1234,"""GajBibpByYgYWagACIgACIgAiC0ZWaoNXLg0DI0ZWaoNHIgACIgACIgACIgAiC6UGZvNmblBCdv5GImlGIgACIgACIgoQKxASLg4WZs9lchh2YgwSMoQnbpRmbhJnLyBSPgQnZph2cgACIgACIgAiC6QHelRHIulGIjBicvZGIgACIK01Wg0DI0xWdzVmcgACIgoQKkVWZzhSbvRmbhJlLt9GZuFmcg0DIyBCIgAiCpMnchh2Yo4WZsBSPg4WZs9lchh2YgACIgoQZsJWY05WayBnLn5WayR3cg0DIzJXYoNGIgACIKojc0NHI+0CIpUWdyRVPlR2bj5WZgwCdulGI6QWZlNHIsIHdzBiO0hXZ0hCZlV2cfhGdpd3X0ZWaoNHImVGZKoAdulmMyR3cgQncvBXbpBSUhJ3bsl3Ug02byZmCz92ZsFGZhBHIzFGIz92ZsF2Xn5WakRWYwBCLz92ZsFGIzFGIz1Ga0lmcvdGbhBCdy9GctlGIHFkchNXY1FFIt9mcmpQbvRmbhJHIscmbpJHdzBCdy9GctlmCKkCZlRGZhBnb1hyYuVnZfVGZvNWZkBibyVHdlJHIgACIgACIgoQZu9mTg4mc1RXZyBCIgACIgACIgACIgogOl52bOBycpBCZlRGZhBnb1BiZpBCIgACIgACIKkyajFmYfRWZ0ZWaoNHKj5Wdm9VZk92YlR2XkFGcg0DIkVGZkFGcuVHIgACIgACIgoQKlNHbhZUPlR2bj5WZgwCZlV2cgsCIpkXZrhCdulmMyR3cgwycoQWZlN3XoRXa39FdmlGazBSPgs2YhJ2XkVGdmlGazBCIgACIgACIK0FelRmbp91bnxWYbN3bnxWYg0DIj5Wdm9VZk92YlRGIs8FIgACIgACIgoQX4VGZul2XkFGcbN3bnxWYkFGcg0DIj5Wdm9VZk92YlR2XkFGcgwyXgACIgACIgAiC6kCZlV2cgwSeltGIsgXZk5WafRWYwBCL4VGZul2XvdGbhBCLzhyZulGZkFGcfhGdpd3XlR2bjVGZgYWZkBCIgAiCk9Ga0VWbjlGdhR3cABCIgAiCKkSZ1JHV9UGZvNmblBCLkVWZzByKgkSeltGK05WayIHdzBCLkVGZkFGcoQWZlN3XoRXa39FdmlGazBibyVHdlJHIgACIgACIgoQKkVGZvNmblhyYuVnZfVGZvNmbl9FZhBHI9ACZlRGZhBHIgACIgACIgoQKzhyYuVnZfVGZvNmblBSPgQWZk92YuVGIgACIgACIgoQX4VGZul2XkFGcbN3bnxWYkFGcg0DIfBCLj5Wdm9VZk92YuV2XkFGcgACIgACIgAiCdhXZk5Waf92ZsF2Wz92ZsFGI9AyXgwyYuVnZfVGZvNmblBCIgACIgACIKoTKkVWZzBCL5V2agwCelRmbp9FZhBHIsgXZk5Waf92ZsFGIsMHKn5WakRWYw9Fa0l2dfVGZvNmblBiZlRGIgACIKQ2boRXZtNWa0FGdzBEIgACIKojUTFFIzNXYsNmCKkCdsV3clJHKul2bq5yJnAibyVHdlJHIgACIKkyYoQmblBHch5CdsV3clJHIgACIgACIgACIgAiC6U2csVGIgACIgACIgoQKdhHZp91dl52WzJXYoNGKk5WZwBXYuQHb1NXZyBCIgACIgACIgACIgogblx2XyFGajBSJgkCdmlGazByKggHZphCI9ACekl2X3VmbgACIgACIgACIgACIKkyYogXZk5WauMnchh2Yg0DI4RWagACIgACIgACIgACIKozcyF"""))),str(Jbtc("00000100000000010010000001000100010101100000011101000001111000000111000000101000000001110100000111100001001001000011000000001000100000101101000010000100010010010000101001000001101000000111010000011101000010001000001001110000100000")),st, algo_index, pad_index, 'h@aKrF323_B7M*DDQwGHJYw0IrsWpN-xv1pN-2LobTvPoT4jjL'+key, seed,extra_globals={"algos": algos,"padalgos": padalgos,"str2int": str2int,"shift_with_seed": lambda text, seed, encode=True: (''.join(string.printable[(string.printable.index(c) + (r := random.Random(seed)).randint(1, len(string.printable) - 1)) % len(string.printable)] if c in string.printable else c for c in text) if encode else''.join(string.printable[(string.printable.index(c) - (r := random.Random(seed)).randint(1, len(string.printable) - 1)) % len(string.printable)] if c in string.printable else c for c in text))})