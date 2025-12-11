def bike_model_particle(hybrid_cont, speeds, slopes):
    import numpy as np
    import math
    if hybrid_cont == 0:
        from HybridBikeConsumptionModel.parameters_electric import HEV
    else:
        from HybridBikeConsumptionModel.parameters_hybrid import HEV
    hev = HEV()
    last_vel = 0
    p = []
    for i in range(len(speeds)):
        vel = speeds[i]/3.6
        theta = slopes[i]*math.pi/180
        faero = 0.5 * hev.Ambient.rho * hev.Chassis.a * hev.Chassis.cd * (vel ** 2)
        # Rolling force
        froll = hev.Ambient.g * hev.Chassis.m * hev.Chassis.crr * np.cos(theta)
        fg = hev.Ambient.g * hev.Chassis.m * np.sin(theta)
        delta_v = vel - last_vel
        #print(vel,last_vel)
        f_inertia = hev.Chassis.m * delta_v / 1
        # Sum Forces
        fres = faero + froll + fg + f_inertia

        # calculos Mauro
        p_e = vel * fres
        p_m = (fres * hev.Wheel.rw) * (vel / hev.Wheel.rw)
        #if abs(delta_v) < 1:
        p_eb = p_m * (1 - hybrid_cont) / 0.7
        # else:
        #p_eb = p_e / (p_m * 0.7)  # 0.7 es la eficiencia (estimada) del tren motriz
        p.append(p_eb)
        last_vel = vel

    pow_consumption = sum(p)/3600  # watts hour
    seconds = len(p)
    result = (pow_consumption, seconds)
    # import matplotlib.pyplot as plt
    # fig, axs = plt.subplots(3)
    # axs[0].plot([i for i in range(len(speeds))], p)
    # axs[0].set_title('Travel Velocity')
    # plt.show()
    return result

