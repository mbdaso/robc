#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Rob�tica Computacional - Curso 2014/2015
# Grado en Ingenier�a Inform�tica (Cuarto)
# Pr�ctica 5:
#     Simulaci�n de robots m�viles holon�micos y no holon�micos.

import sys
from math import *
from robot import robot
import random
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
# ******************************************************************************
# Declaraci�n de funciones

def distancia(a,b):
  # Distancia entre dos puntos (admite poses)
  return np.linalg.norm(np.subtract(a[:2],b[:2]))

def angulo_rel(pose,p):
  # Diferencia angular entre una pose y un punto objetivo 'p'
  w = atan2(p[1]-pose[1],p[0]-pose[0])-pose[2]
  while w >  pi: w -= 2*pi
  while w < -pi: w += 2*pi
  return w

def mostrar_trilateracion(P, M, r):
    plt.ion()
    xmin = -10
    xmax = 10
    ymin = -10
    ymax = 10
    circle1 = plt.Circle((P[0][0], P[0][1]), r[0], color='r', fill=False)
    circle2 = plt.Circle((P[1][0], P[1][1]), r[1], color='g', fill=False)
    circle3 = plt.Circle((P[2][0], P[2][1]), r[2], color='b',  fill=False)
    fig, ax = plt.subplots()
    ax.set_xlim([xmin,xmax])
    ax.set_ylim([ymin,ymax])
    ax.add_artist(circle1)
    ax.add_artist(circle2)
    ax.add_artist(circle3)
    raw_input()

def mostrar(objetivos,ideal,trayectoria):
  # Mostrar objetivos y trayectoria:
  plt.ion() # modo interactivo
  # Fijar los bordes del gr�fico
  objT   = np.array(objetivos).T.tolist()
  trayT  = np.array(trayectoria).T.tolist()
  ideT   = np.array(ideal).T.tolist()
  bordes = [min(trayT[0]+objT[0]+ideT[0]),max(trayT[0]+objT[0]+ideT[0]),
            min(trayT[1]+objT[1]+ideT[1]),max(trayT[1]+objT[1]+ideT[1])]
  centro = [(bordes[0]+bordes[1])/2.,(bordes[2]+bordes[3])/2.]
  radio  = max(bordes[1]-bordes[0],bordes[3]-bordes[2])*.75
  plt.xlim(centro[0]-radio,centro[0]+radio)
  plt.ylim(centro[1]-radio,centro[1]+radio)
  # Representar objetivos y trayectoria
  idealT = np.array(ideal).T.tolist()
  plt.plot(idealT[0],idealT[1],'-g')
  plt.plot(trayectoria[0][0],trayectoria[0][1],'or')
  r = radio * .1
  for p in trayectoria:
    plt.plot([p[0],p[0]+r*cos(p[2])],[p[1],p[1]+r*sin(p[2])],'-r')
    #plt.plot(p[0],p[1],'or')
  objT   = np.array(objetivos).T.tolist()
  plt.plot(objT[0],objT[1],'-.o')
  plt.show()
  raw_input()
  plt.clf()

def get_index_of_n_min_values(values, n):
    values = np.array(values)
    return values.argsort()[:n]

def solve_trilateracion(S, r, last_pos):
    d = S[1][0]
    i = S[2][0]
    j = S[2][1]

    if d == 0.0 or j == 0.0: # Casos division por 0
        print "No hay solucion para " + str(S) + " devolviendo " + str(last_pos[:2])
        return last_pos[:2]

    x = (pow(r[0],2) - pow(r[1],2) + pow(d, 2))/(2*d)
    y = (pow(r[0],2) - pow(r[2],2) + pow(i,2) + pow(j,2))/((2*j)-(i/j)*x)

    return [x,y]


def rotate_points(theta, Q):
    #https://en.wikipedia.org/wiki/Rotation_matrix#In_two_dimensions
    R = [[cos(theta), -sin(theta)],
            [sin(theta), cos(theta)]]
    return [np.dot(R, coord) for coord in Q]

def trilateracion(balizas, real, ideal, mostrar=0):
    # https://stackoverflow.com/questions/16176656/trilateration-and-locating-the-point-x-y-z
    medidas = real.sense(balizas)
    # posiciones de las 3 balizas más cercanas
    indices = get_index_of_n_min_values(medidas[0:-1], 3)
    r = [medidas[i] for i in indices]
    P = [balizas[i] for i in indices] # coordenadas de 3 balizas
    V = np.subtract([0,0], P[0]) # offset
    Q = [np.add(coordenada,V) for coordenada in P] # P + offset
    if (Q[1][1] != 0): # si Q2 no está en el eje x
        # θ = acos(Qx / |Q|)
        theta = acos(Q[1][0]/sqrt(pow(Q[1][0], 2) + pow(Q[1][1], 2)))
        if (Q[1][1] < 0): # Cuadrantes 3 y 4
            theta = 2*pi - theta
        S = rotate_points(-theta, Q) #cerrar el ángulo
        M = solve_trilateracion(S, r, ideal.pose())
        M = rotate_points(theta, [M])[0] #deshacer rotacion
    else:
        M = solve_trilateracion(Q, r, ideal.pose())
    M = np.subtract(M, V) #deshacer offset
    if mostrar:
        mostrar_trilateracion(P, M, r)
    ideal.set(M[0], M[1], medidas[-1])

def localizacion(balizas, real, ideal, centro, radio, mostrar=0):
  # Buscar la localizaci�n m�s probable del robot, a partir de su sistema
  # sensorial, dentro de una regi�n cuadrada de centro "centro" y lado "2*radio".

  # Medidas del robot real
  medidas = real.sense(balizas)
  # Probar moviendo las posiciones del robot ideal
  # En cada posicion de la matriz
  distCelda = float(2.0*float(radio)/float(N))

  def posCasilla(fila, columna, ancho):
     x = columna*ancho + ancho/2
     y = fila*ancho + ancho/2
     return [x,y]

  imagen = [[-1. for x in range(N)] for y in range(N)]

  xyCentro = posCasilla(N/2, N/2, distCelda)
  idealCentro = [centro[0], centro[1]]
  maxPeso = float("-inf")

  # Guardar peso al mover el robot a una casilla de la matriz
  for i in range(N):
      for j in range(N):
          #Mover robot ideal a esa posicion
          #Nueva x:
          xyCasilla = posCasilla(i, j, distCelda)
          xyTransform = np.subtract(xyCasilla, xyCentro)
          xyIdeal = np.add(xyTransform, idealCentro)

          ideal.set(xyIdeal[0], xyIdeal[1], medidas[-1])

          peso = ideal.measurement_prob(medidas, objetivos)

          if (maxPeso < peso):
              maxPeso = peso
              xyMaxPeso = ideal.pose()
          imagen[i][j] = peso

  if mostrar:
    plt.ion() # modo interactivo
    plt.xlim(centro[0]-radio,centro[0]+radio)
    plt.ylim(centro[1]-radio,centro[1]+radio)
    imagen.reverse()
    plt.imshow(imagen,extent=[centro[0]-radio,centro[0]+radio,\
                              centro[1]-radio,centro[1]+radio])
    balT = np.array(balizas).T.tolist();
    plt.plot(balT[0],balT[1],'or',ms=10) #rojo
    plt.plot(ideal.x,ideal.y,'D',c='#ff00ff',ms=10,mew=2) #rosa
    ideal.set(*xyMaxPeso)
    #plt.plot(ideal.x,ideal.y,'D',c='#00ffff',ms=10,mew=2) #cyan
    plt.plot(real.x, real.y, 'D',c='#00ff00',ms=10,mew=2) #verde
    plt.show()
    raw_input()
    plt.clf()
  else:
    ideal.set(*xyMaxPeso)
# ******************************************************************************

# Definici�n del robot:
P_INICIAL = [0.,4.,0.] # Pose inicial (posici�n y orientacion)
V_LINEAL  = .7         # Velocidad lineal    (m/s)
V_ANGULAR = 140.       # Velocidad angular   (�/s)
FPS       = 10.        # Resoluci�n temporal (fps)

HOLONOMICO = 1
GIROPARADO = 0
LONGITUD   = .2

# Definici�n de trayectorias:
trayectorias = [
    [[1,3]],
    [[0,2],[4,2]],
    [[2,4],[4,0],[0,0]],
    [[2,4],[2,0],[0,2],[4,2]],
    [[2+2*sin(.8*pi*i),2+2*cos(.8*pi*i)] for i in range(5)]
    ]

# Definici�n de los puntos objetivo:
if len(sys.argv)<2 or int(sys.argv[1])<0 or int(sys.argv[1])>=len(trayectorias):
  sys.exit(sys.argv[0]+" <�ndice entre 0 y "+str(len(trayectorias)-1)+">, 1 = no mostrar")
objetivos = trayectorias[int(sys.argv[1])]

if len(objetivos) < 3 and (int(sys.argv[2]) == 1):
    sys.exit("No se puede calcular trilateracion con menos de dos puntos")

# Definici�n de constantes:
EPSILON = .1                # Umbral de distancia
V = V_LINEAL/FPS            # Metros por fotograma
W = V_ANGULAR*pi/(180*FPS)  # Radianes por fotograma

########### PESOS BASADOS EN MÁXIMOS PESOS #####################
DIVISOR = 50
PESO_SCRIPT = [ 0.00001,  6.3, 44.38, 85.88, 371.65]
############PESOS MÁXIMOS RECOGIDOS / DIVISOR###################
############# Parámetros para localización #####################
PESO_LOCALIZACION = PESO_SCRIPT[int(sys.argv[1])]             # Minimo peso en measurement prob
N = 21 # Matriz NxN
if (N % 2) is 0: # ==> N tiene que ser impar !!!
    N += 1
RADIO = 0.5
RADIO_INICIAL = 4

#################### ESTADISTICAS ##############################
estadistica_MaxPeso = float("-inf")
estadistica_MinPeso = float("inf")
estadistica_PesoMedio = 0.
estadistica_nMedidas = 0
estadistica_nLocalizaciones = 0
################################################################
ideal = robot()
ideal.set_noise(0,0,.1)   # Ruido lineal / radial / de sensado
#ideal.set(*P_INICIAL)     # operador 'splat'

real = robot()
real.set_noise(.01,.01,0.1)  # Ruido lineal / radial / de sensado
real.set(*P_INICIAL)
localizacion(objetivos, real, ideal, [0,0,0], RADIO_INICIAL, 0)

random.seed(0)
tray_ideal = [ideal.pose()]   # Trayectoria percibida
tray_real = [real.pose()]     # Trayectoria seguida

tiempo  = 0.
espacio = 0.
#random.seed(0)
random.seed(datetime.now())

if (int(sys.argv[2]) == 1):
    print "Método de localización por trilateración"
else:
    print "Localización normal"


for punto in objetivos:
  while distancia(tray_ideal[-1],punto) > EPSILON and len(tray_ideal) <= 1000:
    pose = ideal.pose()

    medidas = real.sense(objetivos)
    peso_medidas = ideal.measurement_prob(medidas, objetivos)

    estadistica_nMedidas += 1
    estadistica_PesoMedio += peso_medidas

    if (estadistica_MinPeso > peso_medidas):
        estadistica_MinPeso = peso_medidas
    elif (estadistica_MaxPeso < peso_medidas):
        estadistica_MaxPeso = peso_medidas

    if (peso_medidas < PESO_LOCALIZACION):
        if (int(sys.argv[2]) == 1):
            trilateracion(objetivos, real, ideal, 0)
        else:
            localizacion(objetivos, real, ideal, ideal.pose(), RADIO, 0)
        estadistica_nLocalizaciones += 1

    w = angulo_rel(pose,punto)
    if w > W:  w =  W
    if w < -W: w = -W
    v = distancia(pose,punto)
    if (v > V): v = V
    if (v < 0): v = 0

    if HOLONOMICO:
      if GIROPARADO and abs(w) > .01:
        v = 0
      ideal.move(w,v)
      real.move(w,v) #se calcula w,v en función del ideal y se mueve el real
    else:
      ideal.move_triciclo(w,v,LONGITUD)
      real.move_triciclo(w,v,LONGITUD)
    tray_ideal.append(ideal.pose())
    tray_real.append(real.pose())

    espacio += v
    tiempo  += 1

if len(tray_ideal) > 1000:
  print "<!> Trayectoria muy larga - puede que no se haya alcanzado la posici�n final."
print "Recorrido: "+str(round(espacio,3))+"m / "+str(tiempo/FPS)+"s"
print "Distancia real al objetivo: "+\
    str(round(distancia(tray_real[-1],objetivos[-1]),3))+"m"
print "Número de localizaciones: " + str(estadistica_nLocalizaciones)
print "Máximo peso: " + str(estadistica_MaxPeso)
print "Mínimo peso: " + str(estadistica_MinPeso)
print "Peso medio: " + str(estadistica_PesoMedio/estadistica_nMedidas)

mostrar(objetivos,tray_ideal,tray_real)  # Representaci�n gr�fica
