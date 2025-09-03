from machine import Pin, PWM
import time
import random
import sys

# LEDs
led1 = Pin(23, Pin.OUT)    # LED 1 en GPIO26
led2 = Pin(22, Pin.OUT)    # LED 2 en GPIO23  
led3 = Pin(21, Pin.OUT)    # LED 3 en GPIO22
leds = [led1, led2, led3]

# Buzzer (usando PWM)
buzzer = PWM(Pin(19))
buzzer.duty(0)

# Botones Jugador 1
btn_led1_p1 = Pin(25, Pin.IN, Pin.PULL_DOWN)  # Para LED1
btn_led2_p1 = Pin(26, Pin.IN, Pin.PULL_DOWN)  # Para LED2
btn_led3_p1 = Pin(27, Pin.IN, Pin.PULL_DOWN)  # Para LED3
btn_buzzer_p1 = Pin(14, Pin.IN, Pin.PULL_DOWN)  # Para Buzzer
botones_jugador1 = [btn_led1_p1, btn_led2_p1, btn_led3_p1, btn_buzzer_p1]

# Botones Jugador 2
btn_led1_p2 = Pin(34, Pin.IN, Pin.PULL_DOWN)  # Para LED1
btn_led2_p2 = Pin(35, Pin.IN, Pin.PULL_DOWN)  # Para LED2
btn_led3_p2 = Pin(32, Pin.IN, Pin.PULL_DOWN)  # Para LED3
btn_buzzer_p2 = Pin(33, Pin.IN, Pin.PULL_DOWN)   # Para Buzzer
botones_jugador2 = [btn_led1_p2, btn_led2_p2, btn_led3_p2, btn_buzzer_p2]

# Botones extras
boton_inicio = Pin(12, Pin.IN, Pin.PULL_DOWN)
boton_fin = Pin(13, Pin.IN, Pin.PULL_DOWN)
boton_fest = Pin(16, Pin.IN, Pin.PULL_DOWN)

# ESTADO
puntuacion_p1 = 0
puntuacion_p2 = 0
ronda_actual = 0
modo_fest = False
juego_activo = False

# Almacenar tiempos de respuesta
tiempos_p1 = []
tiempos_p2 = []
tiempos_totales_p1 = 0
tiempos_totales_p2 = 0

# FUNCIONES

def inicializar_salidas():
    """Apagar todas las salidas"""
    for led in leds:
        led.off()
    buzzer.duty(0)
    print("Salidas inicializadas: LEDs y buzzer apagados")

def beep(t_ms=120, f=1000):
    """Emitir sonido con el buzzer"""
    buzzer.freq(f)
    buzzer.duty(512)
    time.sleep_ms(t_ms)
    buzzer.duty(0)

def antirrebote(pin):
    """Control antirrebote por software"""
    time.sleep_ms(20)
    return pin.value()

def boton_presionado_debounce(botones):
    """Verificar si algún botón fue presionado (con antirrebote)"""
    for idx, boton in enumerate(botones):
        if boton.value() == 1:
            while boton.value() == 1:  # Esperar a que se suelte
                time.sleep_ms(10)
            return idx
    return None

def mostrar_puntuacion():
    """Mostrar puntuación actual"""
    print(f"[PUNTUACION] Ronda {ronda_actual} | J1={puntuacion_p1}  J2={puntuacion_p2}")

# INTERRUPCIÓN: MODO fest
last_irq_time = 0

def interrupcion_fest(pin):
    """Manejar interrupción del botón fest"""
    global modo_fest, last_irq_time
    now = time.ticks_ms()
    
    # Antirrebote
    if time.ticks_diff(now, last_irq_time) < 300:
        return
    
    last_irq_time = now
    modo_fest = not modo_fest
    beep(60, 1500 if modo_fest else 800)
    
    estado = "ACTIVADO" if modo_fest else "DESACTIVADO"
    print(f"[fest] Modo {estado}")

# Configurar interrupción
boton_fest.irq(trigger=Pin.IRQ_RISING, handler=interrupcion_fest)

def generar_estimulo():
    """Genera un estímulo aleatorio (0-3)"""
    return random.randint(0, 3)

def activar_estimulo(estimulo):
    """Activar el estímulo correspondiente"""
    if estimulo < 3:
        leds[estimulo].on()
        print(f"LED {estimulo + 1} activado")
    else:
        buzzer.freq(1200)
        buzzer.duty(512)
        print("BUZZER activado")

def jugar_ronda_normal(num_jugadores):
    """Jugar una ronda normal del juego"""
    global puntuacion_p1, puntuacion_p2, ronda_actual, tiempos_p1, tiempos_p2
    
    ronda_actual += 1
    mostrar_puntuacion()
    
    # Espera aleatoria antes del estímulo
    espera = random.uniform(1.0, 10.0)
    print(f"Esperando {espera:.1f} segundos antes del estímulo...")
    time.sleep(espera)
    
    # Generar y activar estímulo
    estimulo = generar_estimulo()
    activar_estimulo(estimulo)
    tiempo_inicio = time.ticks_ms()
    
    # Variables para respuestas
    respuesta_p1 = None
    respuesta_p2 = None
    tiempo_p1 = None
    tiempo_p2 = None
    
    # Esperar respuestas
    print("Esperando respuestas...")
    
    while True:
        # Verificar botón de parada
        if boton_fin.value():
            print("Juego detenido por el usuario")
            inicializar_salidas()
            return False, None, None
        
        # Jugador 1
        if respuesta_p1 is None:
            btn_idx = boton_presionado_debounce(botones_jugador1)
            if btn_idx is not None:
                tiempo_p1 = time.ticks_diff(time.ticks_ms(), tiempo_inicio)
                respuesta_p1 = btn_idx
                print(f"Jugador 1: Botón {btn_idx} en {tiempo_p1}ms")
        
        # Jugador 2 (solo si hay 2 jugadores)
        if num_jugadores == 2 and respuesta_p2 is None:
            btn_idx = boton_presionado_debounce(botones_jugador2)
            if btn_idx is not None:
                tiempo_p2 = time.ticks_diff(time.ticks_ms(), tiempo_inicio)
                respuesta_p2 = btn_idx
                print(f"Jugador 2: Botón {btn_idx} en {tiempo_p2}ms")
        
        # Salir del bucle si todos han respondido
        if respuesta_p1 is not None and (num_jugadores == 1 or respuesta_p2 is not None):
            break
        
        time.sleep_ms(10)
    
    # Desactivar estímulo
    inicializar_salidas()
    
    # Procesar resultados
    puntos = 1
    
    # Jugador 1
    if respuesta_p1 == estimulo:
        puntuacion_p1 += puntos
        tiempos_p1.append(tiempo_p1)
        print(f"Jugador 1: ¡Correcto! +{puntos} punto")
    else:
        puntuacion_p1 -= 5
        print(f"Jugador 1: Error -5 puntos")
        beep(80, 400)
    
    # Jugador 2
    if num_jugadores == 2:
        if respuesta_p2 == estimulo:
            puntuacion_p2 += puntos
            tiempos_p2.append(tiempo_p2)
            print(f"Jugador 2: ¡Correcto! +{puntos} punto")
        else:
            puntuacion_p2 -= 5
            print(f"Jugador 2: Error -5 puntos")
            beep(80, 400)
    
    mostrar_puntuacion()
    return True, (respuesta_p1, tiempo_p1), (respuesta_p2, tiempo_p2)

def jugar_ronda_fest(num_jugadores, numero_ronda):
    """Jugar una ronda en modo fest"""
    global puntuacion_p1, puntuacion_p2, tiempos_p1, tiempos_p2, tiempos_totales_p1, tiempos_totales_p2
    
    mostrar_puntuacion()
    
    # Espera más corta en modo fest
    espera = random.uniform(0.5, 2.0)
    print(f"[fest R{numero_ronda}] Esperando {espera:.1f} segundos...")
    time.sleep(espera)
    
    # Generar y activar estímulo
    estimulo = generar_estimulo()
    activar_estimulo(estimulo)
    tiempo_inicio = time.ticks_ms()
    
    # Variables para respuestas
    respuesta_p1 = None
    respuesta_p2 = None
    tiempo_p1 = None
    tiempo_p2 = None
    
    # Esperar respuestas
    print("Esperando respuestas...")
    
    while True:
        # Verificar botón de parada
        if boton_fin.value():
            print("Juego detenido por el usuario")
            inicializar_salidas()
            return False, None, None
        
        # Jugador 1
        if respuesta_p1 is None:
            btn_idx = boton_presionado_debounce(botones_jugador1)
            if btn_idx is not None:
                tiempo_p1 = time.ticks_diff(time.ticks_ms(), tiempo_inicio)
                respuesta_p1 = btn_idx
                print(f"Jugador 1: Botón {btn_idx} en {tiempo_p1}ms")
        
        # Jugador 2 (solo si hay 2 jugadores)
        if num_jugadores == 2 and respuesta_p2 is None:
            btn_idx = boton_presionado_debounce(botones_jugador2)
            if btn_idx is not None:
                tiempo_p2 = time.ticks_diff(time.ticks_ms(), tiempo_inicio)
                respuesta_p2 = btn_idx
                print(f"Jugador 2: Botón {btn_idx} en {tiempo_p2}ms")
        
        # Salir del bucle si todos han respondedo
        if respuesta_p1 is not None and (num_jugadores == 1 or respuesta_p2 is not None):
            break
        
        time.sleep_ms(10)
    
    # Desactivar estímulo
    inicializar_salidas()
    
    # Procesar resultados (doble puntos en fest)
    puntos = 2
    
    # Jugador 1
    if respuesta_p1 == estimulo:
        puntuacion_p1 += puntos
        if tiempo_p1 is not None:
            tiempos_p1.append(tiempo_p1)
            tiempos_totales_p1 += tiempo_p1
        print(f"Jugador 1: ¡Correcto! +{puntos} puntos")
    elif respuesta_p1 is not None:
        puntuacion_p1 -= 5
        print(f"Jugador 1: Error -5 puntos")
        beep(80, 400)
    
    # Jugador 2
    if num_jugadores == 2:
        if respuesta_p2 == estimulo:
            puntuacion_p2 += puntos
            if tiempo_p2 is not None:
                tiempos_p2.append(tiempo_p2)
                tiempos_totales_p2 += tiempo_p2
            print(f"Jugador 2: ¡Correcto! +{puntos} puntos")
        elif respuesta_p2 is not None:
            puntuacion_p2 -= 5
            print(f"Jugador 2: Error -5 puntos")
            beep(80, 400)
    
    # Mostrar tiempos de la ronda
    if tiempo_p1 is not None:
        print(f"Jugador 1 - Tiempo R{numero_ronda}: {tiempo_p1}ms")
    if num_jugadores == 2 and tiempo_p2 is not None:
        print(f"Jugador 2 - Tiempo R{numero_ronda}: {tiempo_p2}ms")
    
    mostrar_puntuacion()
    return True, (respuesta_p1, tiempo_p1), (respuesta_p2, tiempo_p2)

def jugar_modo_fest(num_jugadores):
    """Ejecutar las 5 rondas del modo fest"""
    global tiempos_totales_p1, tiempos_totales_p2
    
    tiempos_totales_p1 = 0
    tiempos_totales_p2 = 0
    
    print("\n" + "="*50)
    print("MODO fest ACTIVADO - 5 RONDAS")
    print("Límite: 7000ms en tiempo total para ganar")
    print("="*50)
    
    for i in range(5):
        print(f"\n--- Ronda fest {i+1}/5 ---")
        resultado, resp_p1, resp_p2 = jugar_ronda_fest(num_jugadores, i+1)
        
        if not resultado:
            return False
        
        # Pequeña pausa entre rondas
        if i < 4:
            print("Preparándose para la siguiente ronda...")
            time.sleep(1)
    
    return True

def calcular_promedio_tiempos(tiempos):
    """Calcular promedio de tiempos de respuesta"""
    if not tiempos:
        return float('inf')
    return sum(tiempos) / len(tiempos)

def seleccionar_jugadores_con_botones():
    """Seleccionar número de jugadores usando botones"""
    print("Selecciona número de jugadores:")
    print("Presiona START para 1 jugador")
    print("Presiona fest para 2 jugadores")
    
    while True:
        if boton_inicio.value():
            while boton_inicio.value():
                time.sleep_ms(10)
            return 1
        elif boton_fest.value():
            while boton_fest.value():
                time.sleep_ms(10)
            return 2
        time.sleep_ms(50)

def preguntar_reinicio_con_botones():
    """Preguntar si reiniciar usando botones"""
    print("¿Jugar de nuevo?")
    print("Presiona START para SÍ")
    print("Presiona STOP para NO")
    
    while True:
        if boton_inicio.value():
            while boton_inicio.value():
                time.sleep_ms(10)
            return True
        elif boton_fin.value():
            while boton_fin.value():
                time.sleep_ms(10)
            return False
        time.sleep_ms(50)

def mostrar_resultados_finales(num_jugadores, es_fest=False):
    """Mostrar resultados finales"""
    print("\n" + "="*50)
    print("RESULTADOS FINALES")
    print("="*50)
    
    if es_fest:
        # Lógica para modo fest
        umbral_puntos = 6
        umbral_tiempo = 7000
        
        print(f"Jugador 1 - Puntos: {puntuacion_p1}, Tiempo total: {tiempos_totales_p1}ms")
        if num_jugadores == 2:
            print(f"Jugador 2 - Puntos: {puntuacion_p2}, Tiempo total: {tiempos_totales_p2}ms")
        print(f"Requisito para ganar: {umbral_puntos}+ puntos y ≤{umbral_tiempo}ms")
        
        # Determinar ganador
        gana_p1 = puntuacion_p1 >= umbral_puntos and tiempos_totales_p1 <= umbral_tiempo
        gana_p2 = num_jugadores == 2 and puntuacion_p2 >= umbral_puntos and tiempos_totales_p2 <= umbral_tiempo
        
        if gana_p1 and gana_p2:
            if tiempos_totales_p1 < tiempos_totales_p2:
                ganador = "Jugador 1 GANA (menor tiempo)"
            elif tiempos_totales_p2 < tiempos_totales_p1:
                ganador = "Jugador 2 GANA (menor tiempo)"
            else:
                ganador = "EMPATE"
        elif gana_p1:
            ganador = "Jugador 1 GANA"
        elif gana_p2:
            ganador = "Jugador 2 GANA"
        else:
            ganador = "NADIE GANA EL fest"
    else:
        # Lógica para modo normal
        if puntuacion_p1 > puntuacion_p2:
            ganador = "Jugador 1 GANA"
        elif num_jugadores == 2 and puntuacion_p2 > puntuacion_p1:
            ganador = "Jugador 2 GANA"
        elif num_jugadores == 1:
            ganador = "JUEGO COMPLETADO"
        else:
            # Empate: decidir por tiempo promedio
            prom_p1 = calcular_promedio_tiempos(tiempos_p1)
            prom_p2 = calcular_promedio_tiempos(tiempos_p2)
            
            if prom_p1 < prom_p2:
                ganador = "EMPATE: GANA Jugador 1 (menor tiempo)"
            elif prom_p2 < prom_p1:
                ganador = "EMPATE: GANA Jugador 2 (menor tiempo)"
            else:
                ganador = "EMPATE TOTAL"
    
    print(f"{ganador} | J1={puntuacion_p1}  J2={puntuacion_p2}")
    
    # Mostrar tiempos promedio en modo normal
    if not es_fest:
        if tiempos_p1:
            prom = calcular_promedio_tiempos(tiempos_p1)
            print(f"Jugador 1: {prom:.2f}ms promedio")
        if num_jugadores == 2 and tiempos_p2:
            prom = calcular_promedio_tiempos(tiempos_p2)
            print(f"Jugador 2: {prom:.2f}ms promedio")
    
    # Preguntar por nueva partida usando botones
    return preguntar_reinicio_con_botones()


def main():
    """Función principal del juego"""
    global puntuacion_p1, puntuacion_p2, ronda_actual, juego_activo
    global modo_fest, tiempos_p1, tiempos_p2, tiempos_totales_p1, tiempos_totales_p2
    
    inicializar_salidas()
    
    print("Sistema de medición de reflejos inicializado")
    print("Configuración de pines:")
    print("- LEDs: 23, 22, 21")
    print("- Buzzer: 19")
    print("- START: 12, STOP: 13, fest: 16")
    print("- Jugador 1: 25, 26, 27, 14")
    print("- Jugador 2: 34, 35, 32, 33")
    
    while True:
        # Reiniciar variables
        puntuacion_p1 = 0
        puntuacion_p2 = 0
        ronda_actual = 0
        modo_fest = False
        juego_activo = False
        tiempos_p1 = []
        tiempos_p2 = []
        tiempos_totales_p1 = 0
        tiempos_totales_p2 = 0
        
        print("\n" + "="*50)
        print("SISTEMA DE MEDICIÓN DE REFLEJOS")
        print("="*50)
        
        # Seleccionar número de jugadores con botones
        num_jugadores = seleccionar_jugadores_con_botones()
        print(f"Modo de {num_jugadores} jugador(es) seleccionado")
        
        mostrar_puntuacion()
        print("Presiona START para comenzar...")
        print("Presiona STOP para finalizar")
        print("Presiona fest para cambiar modo")
        
        # Esperar START
        while not boton_inicio.value():
            # Permitir cambiar modo fest mientras se espera START
            time.sleep_ms(30)
        
        # Esperar que se suelte START
        while boton_inicio.value():
            time.sleep_ms(10)
        
        # Iniciar juego según modo
        juego_activo = True
        juego_interrumpido = False
        
        if modo_fest:
            print("\n¡MODO fest ACTIVADO!")
            resultado = jugar_modo_fest(num_jugadores)
            if not resultado:
                juego_interrumpido = True
        else:
            print("\n¡MODO NORMAL!")
            # Jugar rondas normales hasta que el juego sea detenido
            while juego_activo:
                resultado, resp_p1, resp_p2 = jugar_ronda_normal(num_jugadores)
                
                if not resultado:
                    # Juego fue interrumpido con STOP
                    juego_interrumpido = True
                    juego_activo = False
                    break
                
                # Pequeña pausa entre rondas
                print("Preparándose para la siguiente ronda...")
                time.sleep(1)
        
        # Preguntar si reiniciar en todos los casos
        if juego_interrumpido:
            print("\nJuego interrumpido")
        
        print("¿Jugar de nuevo?")
        print("Presiona START para SÍ")
        print("Presiona STOP para NO")
        
        # LIMPIAR EL ESTADO DE LOS BOTONES ANTES DE ESPERAR RESPUESTA
        time.sleep(0.5)  # Pequeña pausa para asegurar
        # Leer y descartar cualquier estado previo de botones
        while boton_inicio.value() or boton_fin.value():
            time.sleep_ms(10)
        
        # Esperar respuesta del usuario (sin estado previo)
        jugar_de_nuevo = None
        while jugar_de_nuevo is None:
            if boton_inicio.value():
                # Esperar a que se suelte el botón
                while boton_inicio.value():
                    time.sleep_ms(10)
                jugar_de_nuevo = True
                print("START presionado - Jugando de nuevo")
                
            elif boton_fin.value():
                # Esperar a que se suelte el botón
                while boton_fin.value():
                    time.sleep_ms(10)
                jugar_de_nuevo = False
                print("STOP presionado - Finalizando juego")
            
            time.sleep_ms(50)
        
        if not jugar_de_nuevo:
            print("¡Gracias por jugar!")
            break
        
        print("Reiniciando juego...")
        time.sleep(1)
main()