from typing import List
import networkx as nx

def inicializar_nfr_emergente(forma_base, campo_coherencia=None):
    """
    Inicializa NFR siguiendo condiciones de emergencia nodal TNFR.
    
    Reemplaza las heurísticas ad-hoc por evaluación estructural canónica.
    """
    # Verificar condiciones de emergencia
    if not cumple_condiciones_emergencia(forma_base, campo_coherencia):
        return None
    
    # Calcular parámetros estructurales
    EPI = evaluar_coherencia_estructural(forma_base)
    νf = calcular_frecuencia_resonante(forma_base)
    Wi_t = generar_matriz_coherencia(forma_base)
    fase = sincronizar_con_campo(campo_coherencia, νf)
    
    # Calcular parámetros derivados
    # ΔNFR: gradiente nodal basado en estabilidad interna de Wi_t
    estabilidad_interna = np.trace(Wi_t) / len(Wi_t)
    ΔNFR = round((1.0 - estabilidad_interna) * 0.5 - 0.1, 3)  # rango típico [-0.1, 0.4]
    
    # Si: índice de sentido basado en coherencia estructural y frecuencia
    Si = round((EPI / 2.5) * (νf / 3.0) * (1.0 - fase), 3)  # decrece con disonancia
    
    # θ: umbral estructural basado en EPI y estabilidad
    θ = round(min(1.0, EPI * estabilidad_interna * 0.4), 3)
    
    # Crear NFR canónico
    nfr = {
        "estado": "activo",
        "glifo": "ninguno",
        "categoria": "ninguna",
        "EPI": EPI,
        "EPI_prev": EPI,
        "EPI_prev2": EPI, 
        "EPI_prev3": EPI,
        "νf": νf,
        "ΔNFR": ΔNFR,
        "Si": Si,
        "θ": θ,
        "Wi_t": Wi_t,
        "fase": fase,
        "simetria_interna": round(estabilidad_interna, 3)
    }
    
    return nfr

def crear_red_desde_datos(datos: List[dict]) -> nx.Graph:
    """Crea red TNFR desde datos estructurados - NUEVA FUNCIÓN"""
    G = nx.Graph()
    campo_coherencia = {}
    
    for nodo_data in datos:
        nodo_id = nodo_data.get('id', f"nodo_{len(G)}")
        
        # Usar inicialización canónica existente
        if 'forma_base' in nodo_data:
            nfr = inicializar_nfr_emergente(nodo_data['forma_base'], campo_coherencia)
            if nfr:
                G.add_node(nodo_id, **nfr)
                campo_coherencia[nodo_id] = nfr
        else:
            # Datos ya procesados
            G.add_node(nodo_id, **nodo_data)
    
    # Usar conectividad canónica existente  
    umbrales, _ = gestionar_conexiones_canonico(G, 0, [])
    return G

def _deben_conectarse_canonico(n1: dict, n2: dict) -> bool:
    """Mejora la lógica existente con umbral áureo"""
    phi = (1 + math.sqrt(5)) / 2  # φ ≈ 1.618
    
    diferencia_vf = abs(n1.get('νf', 1) - n2.get('νf', 1))
    diferencia_fase = abs(n1.get('fase', 0) - n2.get('fase', 0)) % (2 * math.pi)
    
    return (diferencia_vf < 0.01 * phi and 
            diferencia_fase < math.pi / 2)

def simular_emergencia(G, pasos=250):

    umbrales = {
        'θ_min': 0.18,
        'EPI_max_dinamico': 3.0,
        'θ_mutacion': 0.25,
        'θ_colapso': 0.45,
        'bifurcacion_aceleracion': 0.15,
        'EPI_min_coherencia': 0.4,   # ← Añade este valor por defecto
        'θ_conexion': 0.12,
        'EPI_conexion': 1.8,
        'νf_conexion': 0.2,
        'Si_conexion': 0.25,
        'θ_autoorganizacion': 0.35,
        'bifurcacion_gradiente': 0.8,
        'sensibilidad_calculada': 1.0,
        'factor_densidad': 1.0,
        'fase': 'emergencia'
    }


    global historia_Ct
    if 'historia_Ct' not in globals():
        historia_Ct = []
    historia_epi = []
    historia_glifos = ["paso,nodo,glifo"]
    historial_glifos_por_nodo = {}
    G_historia = []
    registro_conexiones = []
    coordinador_temporal = inicializar_coordinador_temporal_canonico()
    bifurcation_manager = BifurcationManagerTNFR()

    historial_temporal = []

    glifo_categoria = {
        "AL": "activador", "EN": "receptor", "IL": "estabilizador",
        "OZ": "disonante", "UM": "acoplador", "RA": "resonador",
        "SHA": "latente", "VAL": "expansivo", "NUL": "contractivo",
        "THOL": "autoorganizador", "ZHIR": "mutante", "NAV": "transicional",
        "REMESH": "recursivo"
    }

    total_pasos = 250

    # Activación mínima inicial si todos están inactivos o silenciosos
    if all(G.nodes[n]["estado"] in ["latente", "silencio"] for n in G.nodes):
        for n in G.nodes:
            if G.nodes[n]["EPI"] > 0.8 and G.nodes[n]["νf"] > 0.5:
                G.nodes[n]["estado"] = "activo"
                G.nodes[n]["glifo"] = "AL"
                break  # activa solo uno, para iniciar pulso

    for paso in range(total_pasos):
        nodos_activos = [n for n in G.nodes if G.nodes[n]["estado"] == "activo"]
        paso_data = [] 

        acoplar_nodos(G)

        # Cálculo de umbrales adaptativos para emergencia nodal
        vf_values = [G.nodes[n]["νf"] for n in G.nodes if G.nodes[n]["estado"] == "activo"]
        dNFR_values = [G.nodes[n]["ΔNFR"] for n in G.nodes if G.nodes[n]["estado"] == "activo"]

        media_vf = np.mean(vf_values) if vf_values else 0
        std_dNFR = np.std(dNFR_values) if dNFR_values else 0

        for n in list(G.nodes):

            nodo = G.nodes[n]
            def valor_valido(x):
                return x is not None and not isinstance(x, str) and not isnan(x)

            for n in list(G.nodes):
                nodo = G.nodes[n]
                
                for clave in ["EPI_prev", "EPI_prev2", "EPI_prev3"]:
                    if not valor_valido(nodo.get(clave)):
                        nodo[clave] = nodo.get("EPI", 1.0)

            if nodo["estado"] == "activo":
                # Dinámica basal influida por νf y sentido
                factor_ruido = random.uniform(0.98, 1.02) + 0.02 * random.uniform(-1, 1) * (1 - nodo["Si"])
                modulador = factor_ruido * (1 + 0.02 * min(nodo.get("νf", 1.0), 5))  # cap νf por seguridad

                nodo["EPI"] *= modulador

                # Evitar NaN o valores extremos
                if not np.isfinite(nodo["EPI"]) or nodo["EPI"] > 10:
                    nodo["EPI"] = 1.0 + random.uniform(-0.05, 0.05)  # reset suave)
                if nodo["EPI"] > 1e4:
                    nodo["EPI"] = 1e4
                nodo["ΔNFR"] += random.uniform(-0.08, 0.08) * (1.1 - nodo["Si"])
                nodo["ΔNFR"] = max(min(nodo["ΔNFR"], 1.5), -1.5) 

                # Condición de apagado nodal si pierde coherencia estructural
                if (
                    nodo["EPI"] < 0.85
                    and abs(nodo["ΔNFR"]) > 0.4
                    and nodo["Si"] < 0.3
                ):
                    nodo["estado"] = "inactivo"

            evaluar_si_nodal(nodo, paso)

            if (
                nodo["estado"] == "silencio"
                and abs(nodo["ΔNFR"] - nodo["νf"]) < 0.05
                and nodo.get("Si", 0) > 0.25
                and nodo.get("d2EPI_dt2", 0) > 0.03
                and not reciente_glifo(n, "NAV", historial_glifos_por_nodo, pasos=6)
            ):
                aplicar_glifo(G, nodo, n, "NAV", historial_glifos_por_nodo, paso)
                historia_glifos.append(f"{paso},{n},NAV")
                nodo["estado"] = "activo"

            if (
                nodo["EPI"] < 0.6
                and abs(nodo["ΔNFR"]) > 0.75
                and nodo["Si"] < 0.25
                and not reciente_glifo(n, "SHA", historial_glifos_por_nodo, pasos=6)
            ):
                aplicar_glifo(G, nodo, n, "SHA", historial_glifos_por_nodo, paso)
                historia_glifos.append(f"{paso},{n},SHA")
                continue

            if (
                nodo["estado"] == "latente"
                and abs(nodo["ΔNFR"]) < 0.05
                and nodo["Si"] > 0.3
                and not reciente_glifo(n, "EN", historial_glifos_por_nodo, pasos=10)
            ):
                aplicar_glifo(G, nodo, n, "EN", historial_glifos_por_nodo, paso)
                historia_glifos.append(f"{paso},{n},EN")

            if (
                nodo["glifo"] == "IL"
                and nodo["Si"] > 0.55
                and nodo["νf"] > 1.25
                and abs(nodo["ΔNFR"]) < 0.15  # Baja necesidad de reorganización
                and not reciente_glifo(n, "RA", historial_glifos_por_nodo, pasos=8)
            ):
                aplicar_glifo(G, nodo, n, "RA", historial_glifos_por_nodo, paso)
                historia_glifos.append(f"{paso},{n},RA")

            vecinos = list(G.neighbors(n))
            if (
                nodo["estado"] == "activo"
                and vecinos
                and sum(1 for v in vecinos if abs(G.nodes[v]["θ"] - nodo["θ"]) < 0.08) >= 2
                and not reciente_glifo(n, "UM", historial_glifos_por_nodo, pasos=8)
            ):
                aplicar_glifo(G, nodo, n, "UM", historial_glifos_por_nodo, paso)
                historia_glifos.append(f"{paso},{n},UM")

            if (
                abs(nodo.get("d2EPI_dt2", 0)) > 0.25
                and nodo["Si"] > 0.6
                and not reciente_glifo(n, "ZHIR", historial_glifos_por_nodo, pasos=10)
            ):
                aplicar_glifo(G, nodo, n, "ZHIR", historial_glifos_por_nodo, paso)
                historia_glifos.append(f"{paso},{n},ZHIR")

            if emergencia_nodal(nodo, media_vf, std_dNFR):
                glifo = glifo_por_estructura(nodo, G)
                if glifo:
                    aplicar_glifo(G, nodo, n, glifo, historial_glifos_por_nodo, paso)
                    historia_glifos.append(f"{paso},{n},{glifo}")
                    nodo["categoria"] = glifo_categoria.get(glifo, "ninguna")

                    # Evaluación glífica con umbrales dinámicos (mejora canónica)
                    vecinos_data = [G.nodes[v] for v in G.neighbors(n)]
                    glifo_dinamico = evaluar_activacion_glifica_dinamica(nodo, umbrales, vecinos_data)

                    if glifo_dinamico and not reciente_glifo(n, glifo_dinamico, historial_glifos_por_nodo, pasos=8):
                        aplicar_glifo(G, nodo, n, glifo_dinamico, historial_glifos_por_nodo, paso)
                        historia_glifos.append(f"{paso},{n},{glifo_dinamico}")

                    glifo_siguiente = transicion_glifica_canonica(nodo)
                    if glifo_siguiente:
                        aplicar_glifo(G, nodo, n, glifo_siguiente, historial_glifos_por_nodo, paso)
                        historia_glifos.append(f"{paso},{n},{glifo_siguiente}")
                        nodo["glifo"] = glifo_siguiente
                        nodo["categoria"] = glifo_categoria.get(glifo_siguiente, "ninguna")

            # Activación estructural de VAL (expansión controlada)
            if (
                nodo["Si"] > 0.8
                and nodo["EPI"] > 1.2
                and abs(nodo["ΔNFR"]) < 0.2
                and nodo.get("dEPI_dt", 0) > 0.15
                and not reciente_glifo(n, "VAL", historial_glifos_por_nodo, pasos=10)
            ):
                if "expansiones_val" not in nodo:
                    nodo["expansiones_val"] = 0

                if nodo["expansiones_val"] < 3:
                    activar_val_si_estabilidad(n, G, paso, historial_glifos_por_nodo)
                    nodo["expansiones_val"] += 1
                else:
                    aplicar_glifo(G, nodo, n, "THOL", historial_glifos_por_nodo, paso)
                    historia_glifos.append(f"{paso},{n},THOL")

            if nodo.get("glifo") == "VAL":
                condiciones_contraccion = (
                    abs(nodo.get("d2EPI_dt2", 0)) < 0.05 and
                    abs(nodo.get("ΔNFR", 0)) < 0.1 and
                    nodo.get("νf", 1.0) < 1.0 and
                    abs(nodo.get("EPI", 0) - nodo.get("EPI_prev", 0)) < 0.01
                )

                if condiciones_contraccion:
                    aplicar_glifo(G, nodo, n, "NUL", historial_glifos_por_nodo, paso)
                    historia_glifos.append(f"{paso},{n},NUL")
                    nodo["glifo"] = "NUL"
                    nodo["categoria"] = glifo_categoria.get("NUL", "ninguna")

            paso_data.append({
                "nodo": n, 
                "paso": paso, 
                "EPI": round(nodo["EPI"], 2)
            })
            nodo["EPI_prev3"] = nodo.get("EPI_prev2", nodo["EPI_prev"])
            nodo["EPI_prev2"] = nodo.get("EPI_prev", nodo["EPI"])
            nodo["EPI_prev"] = nodo["EPI"] if np.isfinite(nodo["EPI"]) else 1.0

            # Cálculo de ∂EPI/∂t = νf · ΔNFR
            dEPI_dt = nodo["νf"] * nodo["ΔNFR"]
            nodo["dEPI_dt"] = dEPI_dt
            if "historial_dEPI_dt" not in nodo:
                nodo["historial_dEPI_dt"] = []
            nodo["historial_dEPI_dt"].append((paso, dEPI_dt))

            # Registrar evolución de νf y ΔNFR
            if "historial_vf" not in nodo:
                nodo["historial_vf"] = []
            if "historial_dNFR" not in nodo:
                nodo["historial_dNFR"] = []

            nodo["historial_vf"].append((paso, nodo["νf"]))
            nodo["historial_dNFR"].append((paso, nodo["ΔNFR"]))

            # Calcular aceleración estructural ∂²EPI/∂t² solo si los valores son válidos
            if all(np.isfinite([nodo.get("EPI", 0), nodo.get("EPI_prev", 0), nodo.get("EPI_prev2", 0)])):
                aceleracion = nodo["EPI"] - 2 * nodo["EPI_prev"] + nodo["EPI_prev2"]
            else:
                aceleracion = 0.0  # O un valor neutro que no active mutaciones erróneas

            nodo["d2EPI_dt2"] = aceleracion

            # Umbral de bifurcación: si se supera, aplicar THOL
            resultado_bifurcaciones = integrar_bifurcaciones_canonicas_en_simulacion(
                G, paso, coordinador_temporal, bifurcation_manager
            )

            # Evaluar contracción si hay disonancia o colapso de sentido (NU´L)
            if nodo.get("estado") == "activo":
                aplicar_contraccion_nul(n, G, paso, historial_glifos_por_nodo)

            # === CONTROL DE EXPANSIÓN INFINITA ===
            if "expansiones_val" not in nodo:
                nodo["expansiones_val"] = 0

            if nodo["expansiones_val"] >= 3:
                continue  # evita expansión si ya lo hizo demasiadas veces

            # Aquí sí puede expandirse:
            activar_val_si_estabilidad(n, G, paso, historial_glifos_por_nodo)
            nodo["expansiones_val"] += 1

            if (
                nodo.get("estado") == "activo"
                and nodo.get("Si", 0) > 0.8
                and nodo.get("EPI", 0) > 1.1
                and abs(nodo.get("ΔNFR", 0)) < 0.25
                and nodo.get("dEPI_dt", 0) > 0.15
                and not reciente_glifo(n, "VAL", historial_glifos_por_nodo, pasos=8)
            ):
                activar_val_si_estabilidad(n, G, paso, historial_glifos_por_nodo)

            # Guardar aceleración para graficar más tarde
            if "historial_aceleracion" not in nodo:
                nodo["historial_aceleracion"] = []
            nodo["historial_aceleracion"].append((paso, aceleracion))

        # Gestión temporal topológica TNFR
        resultado_temporal = integrar_tiempo_topologico_en_simulacion(G, paso, coordinador_temporal)
        historial_temporal.append(resultado_temporal['estadisticas'])

        # Gestión de conexiones con información temporal
        umbrales, estadisticas_conexiones = gestionar_conexiones_canonico(G, paso, historia_Ct)

        # Calcular coherencia total C(t) al final del paso
        C_t = sum(G.nodes[n]["EPI"] for n in G.nodes) / len(G)
        historia_Ct.append((paso, C_t))

        historia_epi.append(paso_data)

        G_snapshot = nx.Graph()
        G_snapshot.add_nodes_from([(n, G.nodes[n].copy()) for n in G.nodes])
        G_snapshot.add_edges_from(G.edges)
        G_historia.append(G_snapshot)

        for nodo_id in list(historial_glifos_por_nodo.keys()):
            glifos = historial_glifos_por_nodo[nodo_id]

            if (
                len(glifos) >= 3 
                and glifos[-1][1] == glifos[-2][1] == glifos[-3][1]
                and abs(G.nodes[nodo_id]["EPI"] - G.nodes[nodo_id]["EPI_prev"]) < 0.05
            ):
                aplicar_glifo(G, G.nodes[nodo_id], nodo_id, "REMESH", historial_glifos_por_nodo, paso)
                historia_glifos.append(f"{paso},{nodo_id},REMESH")

        aplicar_remesh_si_estabilizacion_global(G, historial_glifos_por_nodo, historia_glifos, paso)
        aplicar_remesh_grupal(G, historial_glifos_por_nodo)
        epi_compuestas = detectar_EPIs_compuestas(G, umbrales)
        if algo_se_mueve(G, historial_glifos_por_nodo, paso):
            historial_macronodos, macronodes_info = detectar_macronodos(G, historial_glifos_por_nodo, epi_compuestas, paso)
          
        else:
            macronodes_info = {'nodos': [], 'conexiones': []}

        # Evaluar exceso de VAL y promover reorganización estructural
        for nodo_id, glifos in historial_glifos_por_nodo.items():
            ultimos = [g for _, g in glifos[-6:]]  # últimos 6 glifos del nodo
            if ultimos.count("VAL") >= 4 and "THOL" not in ultimos and "ZHIR" not in ultimos:
                nodo = G.nodes[nodo_id]
                
                # Se decide el glifo correctivo en función de su Si y ΔNFR
                if nodo["Si"] > 0.5 and abs(nodo["ΔNFR"]) < 0.2:
                    aplicar_glifo(G, nodo, nodo_id, "THOL", historial_glifos_por_nodo, paso)
                    historia_glifos.append(f"{paso},{nodo_id},THOL")
                else:
                    aplicar_glifo(G, nodo, nodo_id, "ZHIR", historial_glifos_por_nodo, paso)
                    historia_glifos.append(f"{paso},{nodo_id},ZHIR")

        porcentaje = int((paso + 1) / total_pasos * 100)
        barra = "█" * (porcentaje // 2) + "-" * (50 - porcentaje // 2)
        nodos_activos = [n for n in G.nodes if G.nodes[n]["estado"] == "activo"]

    # Limpiar bifurcaciones obsoletas cada 300 pasos
    if paso % 300 == 0:
        obsoletas = limpiar_bifurcaciones_obsoletas(bifurcation_manager, paso)
    
    lecturas = interpretar_sintaxis_glífica(historial_glifos_por_nodo)

    # Diagnóstico simbólico final
    diagnostico = []
    for nodo in G.nodes:
        nombre = nodo
        datos = G.nodes[nodo]
        glifos_nodo = [g[1] for g in historial_glifos_por_nodo.get(nombre, [])]
        mutó = "ZHIR" in glifos_nodo
        en_epi = any(nombre in grupo["nodos"] for grupo in epi_compuestas)
        lectura = lecturas.get(nombre, {}).get("trayectoria", [])

        diagnostico.append({
            "palabra": nombre,
            "glifos": glifos_nodo,
            "lectura_sintactica": lectura,
            "mutó": mutó,
            "en_epi_compuesta": en_epi,
            "Si": datos.get("Si", 0),
            "estado": datos.get("estado", "latente"),
            "categoría": datos.get("categoria", "sin categoría")
        })

    nodos_pulsantes = detectar_nodos_pulsantes(historial_glifos_por_nodo)

    for nodo_id in nodos_pulsantes:
        nodo = G.nodes[nodo_id]
        historial = historial_glifos_por_nodo.get(nodo_id, [])
        ultimos = [g for _, g in historial][-6:]

        if nodo["glifo"] in ["THOL", "ZHIR", "REMESH"]:
            continue  # ya está mutado o recursivo

        nodo = G.nodes[nodo_id]

        # Evaluar emergente canónico
        if abs(nodo["EPI"] - nodo["EPI_prev"]) < 0.01 and abs(nodo["ΔNFR"]) < 0.05:
            glifo = "REMESH"
        elif abs(nodo.get("θ", 0) - nodo.get("θ_prev", 0)) > 0.2:
            glifo = "ZHIR"
        elif nodo.get("Si", 0) > 0.8 and nodo.get("glifo") == "UM":
            glifo = "RA"
        else:
            glifo = "THOL"

    if nodo_id in G:
        promover_emergente(nodo_id, G, paso, historial_glifos_por_nodo, historia_glifos)

    bifurcation_stats = bifurcation_manager.obtener_estadisticas_bifurcacion()
    return historia_epi, G, epi_compuestas, lecturas, G_historia, historial_glifos_por_nodo, historial_temporal, bifurcation_stats

def aplicar_contraccion_nul(nodo_id, G, paso, historial_glifos_por_nodo):
    nodo = G.nodes[nodo_id]

    condiciones = (
        nodo.get("Si", 1.0) < 0.3 and
        abs(nodo.get("ΔNFR", 0.0)) > 0.8 and
        nodo.get("estado") == "activo" and
        nodo.get("d2EPI_dt2", 0) < -0.05
    )

    if not condiciones:
        return False

    # Aplicar contracción resonante
    nodo["EPI"] = round(nodo["EPI"] * 0.7, 3)
    nodo["estado"] = "latente"
    nodo["glifo"] = "NUL"
    nodo["categoria"] = "contractivo"

    historial_glifos_por_nodo.setdefault(nodo_id, []).append((paso, "NUL"))
    
    return True

def activar_val_si_estabilidad(nodo_id, G, paso, historial_glifos_por_nodo):
    nodo = G.nodes[nodo_id]

    # Restricción por sobreexpansión
    if nodo.get("expansiones_val", 0) >= 3:
        return None

    condiciones = (
        nodo.get("Si", 0) > 0.85 and
        abs(nodo.get("ΔNFR", 0)) < 0.2 and
        nodo.get("dEPI_dt", 0) > 0.18 and
        nodo.get("d2EPI_dt2", 0) > 0.2 and
        nodo.get("estado") == "activo"
    )

    if not condiciones:
        return None

    nuevo_id = f"{nodo_id}_VAL_{random.randint(1000, 9999)}"
    if nuevo_id in G:
        return None

    nuevo_nodo = {
        "EPI": round(nodo["EPI"] * random.uniform(1.0, 1.1), 3),
        "EPI_prev": nodo["EPI"],
        "EPI_prev2": nodo.get("EPI_prev", nodo["EPI"]),
        "EPI_prev3": nodo.get("EPI_prev2", nodo["EPI"]),
        "glifo": "VAL",
        "categoria": "expansivo",
        "estado": "activo",
        "νf": round(nodo["νf"] * random.uniform(1.0, 1.05), 3),
        "ΔNFR": round(nodo["ΔNFR"] * 0.9, 3),
        "θ": round(nodo["θ"] + random.uniform(-0.01, 0.01), 3),
        "Si": nodo["Si"] * 0.98,
        "historial_glifos": [(paso, "VAL")],
        "historial_vf": [(paso, nodo["νf"])],
        "historial_dNFR": [(paso, nodo["ΔNFR"])],
        "historial_dEPI_dt": [(paso, nodo.get("dEPI_dt", 0))],
        "historial_Si": [(paso, nodo["Si"])]
    }

    G.add_node(nuevo_id, **nuevo_nodo)
    G.add_edge(nodo_id, nuevo_id)

    historial_glifos_por_nodo.setdefault(nodo_id, []).append((paso, "VAL"))
    historial_glifos_por_nodo[nuevo_id] = [(paso, "VAL")]

    nodo["expansiones_val"] = nodo.get("expansiones_val", 0) + 1

    return nuevo_id

def aplicar_remesh_grupal(G, historial_glifos_por_nodo):
    nodos_aplicados = set()

    for nodo_id in G.nodes:
        if nodo_id in nodos_aplicados:
            continue

        historial = historial_glifos_por_nodo.get(nodo_id, [])
        if len(historial) < 3:
            continue

        ultimos_glifos = [g for _, g in historial[-3:]]
        if len(set(ultimos_glifos)) != 1:
            continue

        glifo_recurrente = ultimos_glifos[0]

        vecinos = list(G.neighbors(nodo_id))
        grupo = [nodo_id]

        for v_id in vecinos:
            v_nodo = G.nodes[v_id]
            v_hist = historial_glifos_por_nodo.get(v_id, [])
            if len(v_hist) >= 3:
                if [g for _, g in v_hist[-3:]] == ultimos_glifos:
                    if abs(v_nodo.get("θ", 0) - G.nodes[nodo_id].get("θ", 0)) < 0.1:
                        if abs(v_nodo.get("EPI", 0) - v_nodo.get("EPI_prev", v_nodo.get("EPI", 0))) < 0.01:
                            if v_nodo.get("ΔNFR", 1.0) < 0.2:
                                grupo.append(v_id)

        if len(grupo) >= 3:
            for g_id in grupo:
                g_nodo = G.nodes[g_id]
                g_nodo["EPI_prev"] = g_nodo.get("EPI_prev", g_nodo["EPI"])
                g_nodo["EPI_prev2"] = g_nodo.get("EPI_prev2", g_nodo["EPI"])
                g_nodo["EPI"] = (g_nodo["EPI_prev"] + g_nodo["EPI_prev2"]) / 2
                g_nodo["Si"] *= 0.98
                g_nodo["νf"] *= 0.98
                g_nodo["ΔNFR"] *= 0.95
                g_nodo["glifo"] = "REMESH"
                ultimo_paso = historial_glifos_por_nodo[g_id][-1][0] if historial_glifos_por_nodo[g_id] else 0
                historial_glifos_por_nodo[g_id].append((ultimo_paso + 1, "REMESH"))
                nodos_aplicados.add(g_id)

def cumple_condiciones_emergencia(forma_base, campo_coherencia):
    """
    Evalúa si una forma puede generar un NFR según criterios TNFR.
    
    Condiciones de emergencia nodal:
    1. Frecuencia estructural mínima νf > 0.3
    2. Coherencia interna suficiente (estructura no degenerada)  
    3. Acoplamiento posible con campo de coherencia
    """
    if not forma_base or len(forma_base) < 2:
        return False
    
    # Evaluar diversidad estructural interna
    diversidad = len(set(forma_base)) / len(forma_base)
    if diversidad < 0.3:  # demasiado repetitivo
        return False
    
    # Evaluar potencial de frecuencia resonante
    freq_potencial = calcular_frecuencia_resonante(forma_base)
    if freq_potencial < 0.3:  # frecuencia insuficiente para emergencia
        return False
    
    # Evaluar compatibilidad con campo de coherencia
    if campo_coherencia and len(campo_coherencia) > 0:
        coherencia_promedio = np.mean([nodo.get("EPI", 1.0) for nodo in campo_coherencia.values()])
        if coherencia_promedio > 0 and freq_potencial > coherencia_promedio * 2.5:
            return False  # demasiado energético para el campo actual
    
    return True

def evaluar_coherencia_estructural(forma_base):
    """
    Calcula EPI basado en estructura interna real según TNFR.
    
    Evalúa:
    - Simetría funcional de la forma
    - Estabilidad topológica interna  
    - Resistencia a mutaciones
    """
    if not forma_base:
        return 1.0
    
    # Análisis de simetría funcional
    forma_norm = forma_base.lower()
    longitud = len(forma_norm)
    
    # Factor de simetría: evalúa patrones internos
    def calcular_simetria(s):
        centro = len(s) // 2
        if len(s) % 2 == 0:
            izq, der = s[:centro], s[centro:][::-1]
        else:
            izq, der = s[:centro], s[centro+1:][::-1]
        
        coincidencias = sum(1 for a, b in zip(izq, der) if a == b)
        return coincidencias / max(len(izq), 1)
    
    simetria = calcular_simetria(forma_norm)
    
    # Factor de diversidad estructural
    diversidad = len(set(forma_norm)) / longitud
    
    # Factor de estabilidad (resistencia a mutaciones puntuales)
    # Basado en la distribución de caracteres
    contador = Counter(forma_norm)
    entropia = -sum((freq/longitud) * np.log2(freq/longitud) for freq in contador.values())
    estabilidad = min(1.0, entropia / 3.0)  # normalizada
    
    # Factor de coherencia por patrones vocálicos/consonánticos
    vocales = "aeiouáéíóúü"
    patron_vocal = sum(1 for c in forma_norm if c in vocales) / longitud
    coherencia_fonetica = min(1.0, abs(0.4 - patron_vocal) * 2.5)  # óptimo cerca de 40% vocales
    
    # Combinar factores según pesos TNFR
    EPI = (
        0.3 * simetria +           # simetría estructural
        0.25 * diversidad +        # diversidad interna
        0.25 * estabilidad +       # resistencia mutacional
        0.2 * coherencia_fonetica  # coherencia fónica
    )
    
    # Normalizar al rango [0.5, 2.5] típico de EPIs
    EPI_normalizada = 0.5 + EPI * 2.0
    
    return round(EPI_normalizada, 3)

def generar_matriz_coherencia(forma_base):
    """
    Crea matriz Wi(t) para evaluar estabilidad topológica interna.
    
    Modela subnodos internos como caracteres y sus acoplamientos.
    """
    if not forma_base or len(forma_base) < 2:
        return np.array([[1.0]])
    
    longitud = len(forma_base)
    Wi = np.zeros((longitud, longitud))
    
    # Acoplamiento entre caracteres adyacentes (fuerte)
    for i in range(longitud - 1):
        Wi[i][i+1] = Wi[i+1][i] = 0.8
    
    # Acoplamiento entre caracteres similares (débil)
    for i in range(longitud):
        for j in range(i+2, longitud):
            if forma_base[i].lower() == forma_base[j].lower():
                Wi[i][j] = Wi[j][i] = 0.3
    
    # Autocoherencia (diagonal)
    np.fill_diagonal(Wi, 1.0)
    
    # Normalizar filas para que sumen aproximadamente 1
    for i in range(longitud):
        suma_fila = np.sum(Wi[i])
        if suma_fila > 0:
            Wi[i] = Wi[i] / suma_fila
    
    return Wi

def sincronizar_con_campo(campo_coherencia, νf_nodo):
    """
    Calcula fase del nodo respecto al campo de coherencia global.
    
    La fase determina si el nodo está sincronizado o en disonancia
    con el estado actual de la red.
    """
    if not campo_coherencia or len(campo_coherencia) == 0:
        return 0.0  # fase neutra si no hay campo
    
    # Calcular frecuencia promedio del campo
    frecuencias_campo = [nodo.get("νf", 1.0) for nodo in campo_coherencia.values()]
    freq_promedio_campo = np.mean(frecuencias_campo)
    
    # Calcular diferencia de fase basada en frecuencias
    diferencia_freq = abs(νf_nodo - freq_promedio_campo)
    
    # Convertir a fase: diferencias pequeñas = sincronización, grandes = disonancia  
    if diferencia_freq < 0.1:
        fase = 0.0      # sincronización perfecta
    elif diferencia_freq < 0.3:
        fase = 0.25     # sincronización parcial
    elif diferencia_freq < 0.6:
        fase = 0.5      # neutral
    elif diferencia_freq < 1.0:
        fase = 0.75     # disonancia parcial
    else:
        fase = 1.0      # disonancia completa
    
    return round(fase, 3)

__all__ = [
    'inicializar_nfr_emergente',
    '_deben_conectarse_canonico',
    'crear_red_desde_datos', 
    'simular_emergencia',
    'aplicar_contraccion_nul',
    'activar_val_si_estabilidad',
    'aplicar_remesh_grupal',
    'cumple_condiciones_emergencia',
    'evaluar_coherencia_estructural',
    'generar_matriz_coherencia',
    'sincronizar_con_campo'
]
