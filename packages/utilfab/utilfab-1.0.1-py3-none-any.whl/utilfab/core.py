# ---------------------------------------
# Librería: utilFAB v1.0
# Autor: V4FAB
# Descripción: Utilidades generales para procesamiento de texto, decisiones y formato
# ---------------------------------------

def printEsp(n=1):
    """Imprime n líneas en blanco."""
    for _ in range(n):
        print("")

def alyz(q):
    """Devuelve el tipo del objeto q."""
    return {'tipo': type(q)}

def decisionMake(ask, options=None):
    """
    Muestra un menú de opciones numeradas y devuelve la opción elegida como número.
    Si options es None o False, se usarán ["Sí", "No"] por defecto.
    """
    if not options:
        options = ["Sí", "No"]

    def printOptions(options):
        validOpt = []
        for i, option in enumerate(options, start=1):
            print(f"{i}: {option}")
            validOpt.append(i)
        return validOpt

    validOpt = printOptions(options)

    try:
        decision = int(input(ask + " "))
    except:
        decision = None

    while type(decision) is not int or decision not in validOpt:
        printEsp()
        print("Por favor, ingresá una opción válida (número).")
        try:
            decision = int(input(ask + " "))
        except:
            decision = None

    return decision

def pb(way, q):
    """
    Manipulación de palabras:
    way:
        - 'separar', 1, 'break', 'sep' → separar en palabras
        - 'juntar', 2, 'join', 'j' → unir palabras
        - 'inv', 'turn', 3 → invertir letras
        - 'low' → minúsculas
        - 'up'  → mayúsculas
    """
    if way in ['separar', 1, 'break', 'sep']:
        if isinstance(q, str):
            return q.strip().split()
        else:
            return []

    elif way in ['juntar', 2, 'join', 'j']:
        if isinstance(q, list):
            return " ".join(q)
        else:
            return str(q)
    elif way in ['inv', 'turn', 3]:
      new = []
      if alyz(q)['tipo'] == list:
        for p in q:
          new.append(pb('inv', q))
        return new.reverse()
      else:
        return q[::-1]
    elif way in ['low', 'up']:
        if isinstance(q, str):
            return q.lower() if way == 'low' else q.upper()
        elif isinstance(q, list):
            mod = [w.lower() if way == 'low' else w.upper() for w in q]
            return mod
        else:
            return q

    return q  # default fallback

def test(key):
  """
  Esto es para probar la libreria...
  - key == 'key'
  """
  if key == 'key':
    print(1)
    printEsp(2)
    print(2)
    printEsp(2)
    d = decisionMake("Si o no?: ", 0)
    print(d)
    printEsp(1)
    d2 = decisionMake("¿Cual es la capital de Argentina?", ["C.A.B.A.", "Cordoba", "Entre Rios", "Salta", "Jujuy"])
    print(d2)
    opc = ["C.A.B.A.", "Cordoba", "Entre Rios", "Salta", "Jujuy"]
    while not d2 == 1:
      printEsp(2)
      d = decisionMake("Incorrecto! ¿Quieres intentarlo nuevamente?:  ")
      if d == 1:
        d2 = decisionMake("¿Cual es la capital de Argentina?", opc)
      else: break
    msg = "Correcto!, la capital de Argentina es C.A.B.A."
    if d2 == 1:
      print(msg)
    else:
      print("Has decidido saltarte esta pregunta.")

    printEsp(3)
    print(pb('sep', msg))
    print(opc)
    print(pb('j', opc))
    printEsp(2)
    print(pb('up', msg))
    print(pb('up', opc))
    print(pb('j', pb('up', opc)))

    printEsp(2)
    print("Prueba finalizada")
    return True

# test(key='key')