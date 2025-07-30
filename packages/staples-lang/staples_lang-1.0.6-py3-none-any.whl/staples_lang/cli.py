import argparse

def run(code):
    if len(code) % 8 == 0:
        if len(code) % 2 == 0:
            oldcode = code
            code = code.replace("[", "0")
            code = code.replace("{", "1")
            midpoint = len(oldcode) // 2
            checksum = str(code)[midpoint:][::-1]
            checksum = checksum.replace("]", "[")
            checksum = checksum.replace("}", "{")
            oldcode = str(oldcode)[:midpoint]
            if str(checksum) == str(oldcode):
                executable = ""
                for i in range(0, midpoint, 8):
                    executable += chr(int(code[i:i+8], 2))
                try:
                    context = {
                        "__name__": "__main__",
                        "__file__": "<staples_virtual_file>",
                        "__builtins__": __builtins__
                    }
                    exec(executable, context, context)
                except Exception as e:
                    print(f"""ERR: {e}""")
            else:
                return "ERR: Incorrect Checksum"
        else:
            return "ERR: Syntax"
    else:
        return "ERR: Syntax"
    
def convert(code):
    staples = ""
    for i in code:
        staples += format(ord(i), '08b')
    staples = staples.replace("0","[")
    staples = staples.replace("1","{")
    end = staples[::-1]
    end = end.replace("[","]")
    end = end.replace("{","}")
    output = staples + end
    return str(output)

def main():
    parser = argparse.ArgumentParser(description="Staples Language")
    parser.add_argument('command', choices=['runfile', 'compilefile','runstring', 'compilestring'], help='Command to run')
    parser.add_argument('input', help='Path/String to process')

    args = parser.parse_args()

    if args.command == 'runfile':
        with open(str(args.input), "r") as f:
            to_run = f.read()
        result = run(to_run)
        if result is not None:
            print(result)
    elif args.command == 'compilefile':
        with open(str(args.input), "r") as f:
            to_compile = f.read()
        result = convert(str(to_compile))
        with open(str(args.input) + ".staples", "w") as f:
            f.write(str(result))
    elif args.command == 'runstring':
        to_run = args.input
        result = run(to_run)
        if result is not None:
            print(result)
    elif args.command == 'compilestring':
        to_compile = args.input
        result = convert(str(to_compile))
        print(result)
if __name__ == "__main__":
    main()
