import string


def ceasar_encode(input_string, rot):
    input_string = input_string.lower()
    # input_string = input_string.replace(" ", "")
    chars = list("abcdefghijklmnopqrstuvwxyz")
    return "".join(chars[(chars.index(c) + rot) % len(chars)] for c in input_string)


s = "WDkbfasdbmbtuquefpuqiueeqzeotmrfpqdhqdeotxgqeeqxgzshazuzradymfuazqzgypqdqzhqdfdmgxuotwwqufuzfqsdufmqfgzpmgftqzfulufmqflgsqimqtdxquefqzpmnquiqdpqzymftqymfueotqhqdrmtdqzquzsqeqflfgypmfqzhadgznqrgsfqylgsdurrlgeotgqflqzpuqwdkbfaxasuqducsqsqzgyrmeefquzndqufugqerqxpgz"
print(ceasar_encode(s, 14))
