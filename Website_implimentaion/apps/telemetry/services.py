import math
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from apps.plant.models import Plant, Device, DeviceType
from .models import (
    InverterObservation, MFMObservation, WMSObservation,
    DeviceLatest, CommunicationStatus, DataQuality, AlarmEvent, AlarmSeverity
)

class PlantCalculations:
    @staticmethod
    def specific_yield(ac_energy_kwh, dc_capacity_kwp):
        """Specific Yield = AC Energy (kWh) / Installed DC Capacity (kWp) [kWh/kWp]"""
        if not dc_capacity_kwp or dc_capacity_kwp <= 0:
            return 0.0
        return round(ac_energy_kwh / dc_capacity_kwp, 2)

    @staticmethod
    def cuf(ac_energy_kwh, ac_capacity_kw, hours=24.0):
        """CUF (%) = 100 * E_AC / (P_AC * T_hours)"""
        if not ac_capacity_kw or ac_capacity_kw <= 0 or hours <= 0:
            return 0.0
        return round((ac_energy_kwh / (ac_capacity_kw * hours)) * 100.0, 2)

    @staticmethod
    def pr(ac_energy_kwh, dc_capacity_kwp, poa_insolation_kwh_m2, g_ref=1.0):
        """PR (%) = 100 * E_AC / (P_DC * H_POA / G_ref)"""
        if not dc_capacity_kwp or not poa_insolation_kwh_m2 or dc_capacity_kwp <= 0 or poa_insolation_kwh_m2 <= 0:
            return None
        denom = dc_capacity_kwp * (poa_insolation_kwh_m2 / g_ref)
        if denom <= 0:
            return None
        val = (ac_energy_kwh / denom) * 100.0
        return round(min(val, 100.0), 2)

    @staticmethod
    def environmental_metrics(ac_energy_kwh):
        """Calculates environmental savings from solar generation:
        - CO2 avoided: ~0.82 kg CO2 / kWh
        - Coal saved: ~0.40 kg coal / kWh
        - Equivalent trees: ~0.040 trees / kWh
        """
        co2_kg = ac_energy_kwh * 0.82
        coal_kg = ac_energy_kwh * 0.40
        trees = ac_energy_kwh * 0.040
        return {
            'co2_saved_tonnes': round(co2_kg / 1000.0, 2),
            'co2_saved_kg': round(co2_kg, 1),
            'coal_saved_tonnes': round(coal_kg / 1000.0, 2),
            'trees_planted': int(round(trees))
        }


def seed_plant_and_devices():
    """Initializes the plant topology with 13 Sungrow Inverters, 2 MFMs, 1 WMS."""
    plant, _ = Plant.objects.get_or_create(
        name="SATs Solar Plant",
        defaults={
            'organization': "SATs (Semiconductor Analysis and Testing Solutions)",
            'timezone': "Asia/Kolkata",
            'ac_capacity_kw': 3900.0,
            'dc_capacity_kwp': 4640.0,
            'expected_daily_yield_kwh': 18500.0
        }
    )
    
    # 13 Inverters (INV-01 to INV-13)
    inverters = []
    inv_ac = 300.0  # 300 kW * 13 = 3900 kW
    inv_dc = 356.92 # 356.92 * 13 = 4640 kWp
    
    for i in range(1, 14):
        dev_id = f"INV-{i:02d}"
        inv, _ = Device.objects.get_or_create(
            plant=plant,
            device_id=dev_id,
            defaults={
                'name': f"Inverter {i:02d}",
                'device_type': DeviceType.INVERTER,
                'manufacturer': "Sungrow",
                'model': "SG300HX",
                'zone': f"Zone {'A' if i <= 7 else 'B'}",
                'ac_capacity_kw': inv_ac,
                'dc_capacity_kwp': inv_dc,
                'poll_interval_seconds': 30,
                'display_order': i
            }
        )
        inverters.append(inv)
        
    # 2 MFMs: LT Meter and Outgoing Meter
    mfm_lt, _ = Device.objects.get_or_create(
        plant=plant,
        device_id="MFM-LT",
        defaults={
            'name': "LT Meter",
            'device_type': DeviceType.MFM,
            'manufacturer': "Schneider Electric",
            'model': "PM8000",
            'zone': "LT Switchgear Room",
            'ac_capacity_kw': 3900.0,
            'dc_capacity_kwp': 0.0,
            'display_order': 20
        }
    )
    
    mfm_out, _ = Device.objects.get_or_create(
        plant=plant,
        device_id="MFM-OUT",
        defaults={
            'name': "Outgoing MFM (Main Export/Import)",
            'device_type': DeviceType.MFM,
            'manufacturer': "Secure Meters",
            'model': "Premier 300",
            'zone': "Main Substation Yard",
            'ac_capacity_kw': 3900.0,
            'dc_capacity_kwp': 0.0,
            'display_order': 21
        }
    )
    
    # 1 WMS (Weather Monitoring Station)
    wms, _ = Device.objects.get_or_create(
        plant=plant,
        device_id="WMS-01",
        defaults={
            'name': "Weather Monitoring Station",
            'device_type': DeviceType.WMS,
            'manufacturer': "Kipp & Zonen",
            'model': "SMP10-A",
            'zone': "Meteorological Mast",
            'ac_capacity_kw': 0.0,
            'dc_capacity_kwp': 0.0,
            'display_order': 30
        }
    )
    
    return plant, inverters, mfm_lt, mfm_out, wms


def seed_reference_telemetry(target_time=None):
    """
    Seeds a coherent reproducible dataset including the reference snapshot:
    - Inverter total energy: 11,921.30 kWh
    - Inverter lifetime: 1,567,546.00 kWh
    - Active power: 3,573.96 kW
    - GHI: 905 W/m², GTI: 1,165 W/m²
    - Humidity: 23.10 %RH
    - Ambient temp: 38.1 °C, Module temp: 51.0 °C
    """
    plant, inverters, mfm_lt, mfm_out, wms = seed_plant_and_devices()
    
    if target_time is None:
        target_time = timezone.now()
        
    with transaction.atomic():
        # 1. Weather reading
        wms_obs, _ = WMSObservation.objects.get_or_create(
            device=wms,
            timestamp=target_time,
            defaults={
                'ambient_temp': 38.1,
                'module_temp': 51.0,
                'humidity': 23.1,
                'ghi': 905.0,
                'gti': 1165.0,
                'insolation_today_ghi': 4.82,
                'insolation_today_gti': 5.94,
                'wind_speed': 3.4,
                'wind_direction': 210.0,
                'diffuse_irradiance': 185.0,
                'rainfall': 0.0,
                'cloud_cover': 8.0,
                'quality': DataQuality.VALID
            }
        )
        
        DeviceLatest.objects.update_or_create(
            device=wms,
            defaults={
                'last_contact_time': target_time,
                'last_valid_time': target_time,
                'status': CommunicationStatus.ONLINE,
                'operating_state': "Normal",
                'active_power': 0.0,
                'daily_yield': 0.0,
                'lifetime_yield': 0.0,
                'temperature': 38.1,
                'alarm_active': False,
                'raw_snapshot': {
                    'ambient_temp': 38.1, 'module_temp': 51.0, 'humidity': 23.1,
                    'ghi': 905.0, 'gti': 1165.0
                }
            }
        )
        
        # 2. Inverters (Total Active Power: 3,573.96 kW, Total Today: 11,921.30 kWh, Lifetime: 1,567,546.00 kWh)
        total_p_ac = 3573.96
        total_e_today = 11921.30
        total_e_life = 1567546.00
        
        # Distribute across 13 inverters
        inv_power = round(total_p_ac / 13.0, 2)
        inv_daily = round(total_e_today / 13.0, 2)
        inv_life = round(total_e_life / 13.0, 2)
        
        for idx, inv in enumerate(inverters):
            # Slight realistic variations while strictly summing to plant totals
            if idx == 12:
                # Last inverter takes remainder for exact match
                cur_power = round(total_p_ac - (inv_power * 12), 2)
                cur_daily = round(total_e_today - (inv_daily * 12), 2)
                cur_life = round(total_e_life - (inv_life * 12), 2)
            else:
                cur_power = inv_power
                cur_daily = inv_daily
                cur_life = inv_life
                
            cur_dc_power = round(cur_power / 0.984, 2)  # ~98.4% efficiency
            vdc = 720.0 + (idx % 4) * 8.0
            idc = round((cur_dc_power * 1000.0) / vdc, 2)
            
            # MPPT Voltages and Currents (12 channels)
            mppt_v = [round(vdc + (c * 1.5), 1) for c in range(12)]
            mppt_i = [round(idc / 12.0 + (c * 0.1), 2) for c in range(12)]
            
            # 25 String currents
            string_i = [round(idc / 25.0 + ((s % 5) * 0.05), 2) for s in range(25)]
            
            InverterObservation.objects.get_or_create(
                device=inv,
                timestamp=target_time,
                defaults={
                    'vdc': vdc,
                    'idc': idc,
                    'v_ry': 800.0,
                    'v_yb': 800.0,
                    'v_br': 800.0,
                    'i_r': round(cur_power * 1000 / (math.sqrt(3) * 800 * 0.99), 1),
                    'i_y': round(cur_power * 1000 / (math.sqrt(3) * 800 * 0.99), 1),
                    'i_b': round(cur_power * 1000 / (math.sqrt(3) * 800 * 0.99), 1),
                    'power_factor': 0.99,
                    'frequency': 50.02,
                    'active_power': cur_power,
                    'reactive_power': round(cur_power * 0.05, 2),
                    'dc_power': cur_dc_power,
                    'daily_yield': cur_daily,
                    'lifetime_yield': cur_life,
                    'insulation_resistance': 1250.0,
                    'temperature': round(48.5 + (idx % 3), 1),
                    'operating_status': "Running",
                    'alarm_code': "0",
                    'mppt_data': {'v': mppt_v, 'i': mppt_i},
                    'string_currents': string_i,
                    'quality': DataQuality.VALID
                }
            )
            
            DeviceLatest.objects.update_or_create(
                device=inv,
                defaults={
                    'last_contact_time': target_time,
                    'last_valid_time': target_time,
                    'status': CommunicationStatus.ONLINE,
                    'operating_state': "Running",
                    'active_power': cur_power,
                    'daily_yield': cur_daily,
                    'lifetime_yield': cur_life,
                    'temperature': round(48.5 + (idx % 3), 1),
                    'conversion_efficiency': round((cur_power / cur_dc_power) * 100, 2),
                    'alarm_active': False,
                    'raw_snapshot': {'active_power': cur_power, 'daily_yield': cur_daily}
                }
            )
            
        # 3. MFMs: LT Meter and Outgoing MFM
        # Outgoing MFM measures exported power at substation (accounting for transformer/cable transmission)
        out_power = round(total_p_ac * 0.988, 2)  # ~3531 kW export
        out_energy_today = round(total_e_today * 0.988, 2)
        out_energy_life = round(total_e_life * 0.988, 2)
        
        MFMObservation.objects.get_or_create(
            device=mfm_out,
            timestamp=target_time,
            defaults={
                'active_power': out_power,
                'reactive_power': 120.5,
                'apparent_power': round(math.sqrt(out_power**2 + 120.5**2), 1),
                'v_ll': 11.0, # 11 kV grid
                'v_ry': 6350.0,
                'v_yb': 6350.0,
                'v_br': 6350.0,
                'i_r': 185.2,
                'i_y': 184.9,
                'i_b': 185.6,
                'i_neutral': 1.2,
                'frequency': 50.01,
                'power_factor': 0.998,
                'import_energy_today': 12.5,
                'export_energy_today': out_energy_today,
                'import_energy_lifetime': 1840.0,
                'export_energy_lifetime': out_energy_life,
                'quality': DataQuality.VALID
            }
        )
        
        DeviceLatest.objects.update_or_create(
            device=mfm_out,
            defaults={
                'last_contact_time': target_time,
                'last_valid_time': target_time,
                'status': CommunicationStatus.ONLINE,
                'operating_state': "Normal",
                'active_power': out_power,
                'daily_yield': out_energy_today,
                'lifetime_yield': out_energy_life,
                'temperature': 32.0,
                'alarm_active': False,
                'raw_snapshot': {'export_power': out_power, 'export_today': out_energy_today}
            }
        )
        
        # LT MFM
        MFMObservation.objects.get_or_create(
            device=mfm_lt,
            timestamp=target_time,
            defaults={
                'active_power': round(total_p_ac * 0.995, 2),
                'reactive_power': 95.0,
                'apparent_power': round(total_p_ac * 0.997, 2),
                'v_ll': 0.80, # 800 V LT bus
                'v_ry': 800.0,
                'v_yb': 800.0,
                'v_br': 800.0,
                'i_r': 2580.0,
                'i_y': 2575.0,
                'i_b': 2582.0,
                'i_neutral': 4.1,
                'frequency': 50.02,
                'power_factor': 0.995,
                'import_energy_today': 5.2,
                'export_energy_today': round(total_e_today * 0.995, 2),
                'import_energy_lifetime': 850.0,
                'export_energy_lifetime': round(total_e_life * 0.995, 2),
                'quality': DataQuality.VALID
            }
        )
        
        DeviceLatest.objects.update_or_create(
            device=mfm_lt,
            defaults={
                'last_contact_time': target_time,
                'last_valid_time': target_time,
                'status': CommunicationStatus.ONLINE,
                'operating_state': "Normal",
                'active_power': round(total_p_ac * 0.995, 2),
                'daily_yield': round(total_e_today * 0.995, 2),
                'lifetime_yield': round(total_e_life * 0.995, 2),
                'temperature': 34.0,
                'alarm_active': False,
                'raw_snapshot': {'active_power': round(total_p_ac * 0.995, 2)}
            }
        )


def seed_historical_telemetry(days=1):
    """Generates continuous historical interval data (every 15 minutes) for charts and reports."""
    plant, inverters, mfm_lt, mfm_out, wms = seed_plant_and_devices()
    now = timezone.now()
    
    # Generate 15-minute intervals for today starting from 06:00 to current hour
    start_of_day = now.replace(hour=6, minute=0, second=0, microsecond=0)
    intervals = []
    curr = start_of_day
    while curr <= now:
        intervals.append(curr)
        curr += timedelta(minutes=15)
        
    with transaction.atomic():
        accumulated_inverter_kwh = 0.0
        
        for t in intervals:
            # Solar curve simulation: bell curve peak at 12:30 PM
            hour_float = t.hour + t.minute / 60.0
            if 6.0 <= hour_float <= 18.5:
                # Bell curve
                peak_factor = math.sin((hour_float - 6.0) / 12.5 * math.pi)
                ghi = round(max(0.0, 950.0 * peak_factor * (0.95 + random.uniform(0, 0.1))), 1)
                gti = round(max(0.0, 1180.0 * peak_factor * (0.95 + random.uniform(0, 0.1))), 1)
                total_power = round(max(0.0, 3650.0 * peak_factor * (0.96 + random.uniform(0, 0.08))), 2)
            else:
                ghi = 0.0
                gti = 0.0
                total_power = 0.0
                
            interval_energy = round((total_power * 0.25), 2)  # 15 minutes = 0.25 hours
            accumulated_inverter_kwh += interval_energy
            
            # WMS
            WMSObservation.objects.get_or_create(
                device=wms,
                timestamp=t,
                defaults={
                    'ambient_temp': round(24.0 + 15.0 * peak_factor if 'peak_factor' in locals() else 24.0, 1),
                    'module_temp': round(26.0 + 26.0 * peak_factor if 'peak_factor' in locals() else 26.0, 1),
                    'humidity': round(45.0 - 20.0 * peak_factor if 'peak_factor' in locals() else 50.0, 1),
                    'ghi': ghi,
                    'gti': gti,
                    'insolation_today_ghi': round(accumulated_inverter_kwh / 2500.0, 2),
                    'insolation_today_gti': round(accumulated_inverter_kwh / 2000.0, 2),
                    'wind_speed': round(2.0 + random.uniform(0, 2.5), 1),
                    'wind_direction': 210.0,
                    'diffuse_irradiance': round(ghi * 0.2, 1),
                    'rainfall': 0.0,
                    'cloud_cover': 5.0,
                    'quality': DataQuality.VALID
                }
            )
            
            # Inverters
            inv_p = round(total_power / 13.0, 2)
            inv_e = round(accumulated_inverter_kwh / 13.0, 2)
            for i, inv in enumerate(inverters):
                vdc = round(700.0 + 40.0 * peak_factor if 'peak_factor' in locals() else 650.0, 1)
                idc = round((inv_p * 1000.0 / vdc) if vdc > 0 else 0.0, 2)
                InverterObservation.objects.get_or_create(
                    device=inv,
                    timestamp=t,
                    defaults={
                        'vdc': vdc,
                        'idc': idc,
                        'v_ry': 800.0,
                        'v_yb': 800.0,
                        'v_br': 800.0,
                        'i_r': round(inv_p * 1000 / (math.sqrt(3) * 800 * 0.99), 1) if inv_p > 0 else 0.0,
                        'i_y': round(inv_p * 1000 / (math.sqrt(3) * 800 * 0.99), 1) if inv_p > 0 else 0.0,
                        'i_b': round(inv_p * 1000 / (math.sqrt(3) * 800 * 0.99), 1) if inv_p > 0 else 0.0,
                        'power_factor': 0.99,
                        'frequency': round(50.0 + random.uniform(-0.03, 0.03), 2),
                        'active_power': inv_p,
                        'reactive_power': round(inv_p * 0.04, 2),
                        'dc_power': round(inv_p / 0.984, 2) if inv_p > 0 else 0.0,
                        'daily_yield': inv_e,
                        'lifetime_yield': 120500.0 + inv_e,
                        'insulation_resistance': 1200.0,
                        'temperature': round(35.0 + 18.0 * peak_factor if 'peak_factor' in locals() else 35.0, 1),
                        'operating_status': "Running" if inv_p > 0 else "Standby",
                        'alarm_code': "0",
                        'mppt_data': {
                            'v': [round(vdc + (c * 1.2), 1) for c in range(12)],
                            'i': [round(idc / 12.0 + (c * 0.08), 2) for c in range(12)]
                        },
                        'string_currents': [round(idc / 25.0 + ((s % 5) * 0.04), 2) for s in range(25)],
                        'quality': DataQuality.VALID
                    }
                )
                
            # MFM Outgoing
            out_p = round(total_power * 0.988, 2)
            out_e = round(accumulated_inverter_kwh * 0.988, 2)
            MFMObservation.objects.get_or_create(
                device=mfm_out,
                timestamp=t,
                defaults={
                    'active_power': out_p,
                    'reactive_power': round(out_p * 0.03, 2),
                    'apparent_power': round(out_p * 1.002, 2),
                    'v_ll': 11.0,
                    'v_ry': 6350.0,
                    'v_yb': 6350.0,
                    'v_br': 6350.0,
                    'i_r': round(out_p * 1000 / (math.sqrt(3) * 11000 * 0.998), 1) if out_p > 0 else 0.0,
                    'i_y': round(out_p * 1000 / (math.sqrt(3) * 11000 * 0.998), 1) if out_p > 0 else 0.0,
                    'i_b': round(out_p * 1000 / (math.sqrt(3) * 11000 * 0.998), 1) if out_p > 0 else 0.0,
                    'i_neutral': 1.0,
                    'frequency': 50.0,
                    'power_factor': 0.998,
                    'import_energy_today': 12.0,
                    'export_energy_today': out_e,
                    'import_energy_lifetime': 1840.0,
                    'export_energy_lifetime': 1548000.0 + out_e,
                    'quality': DataQuality.VALID
                }
            )
            
            # MFM LT
            lt_p = round(total_power * 0.995, 2)
            lt_e = round(accumulated_inverter_kwh * 0.995, 2)
            MFMObservation.objects.get_or_create(
                device=mfm_lt,
                timestamp=t,
                defaults={
                    'active_power': lt_p,
                    'reactive_power': round(lt_p * 0.03, 2),
                    'apparent_power': round(lt_p * 1.002, 2),
                    'v_ll': 0.80,
                    'v_ry': 800.0,
                    'v_yb': 800.0,
                    'v_br': 800.0,
                    'i_r': round(lt_p * 1000 / (math.sqrt(3) * 800 * 0.995), 1) if lt_p > 0 else 0.0,
                    'i_y': round(lt_p * 1000 / (math.sqrt(3) * 800 * 0.995), 1) if lt_p > 0 else 0.0,
                    'i_b': round(lt_p * 1000 / (math.sqrt(3) * 800 * 0.995), 1) if lt_p > 0 else 0.0,
                    'i_neutral': 3.5,
                    'frequency': 50.0,
                    'power_factor': 0.995,
                    'import_energy_today': 4.5,
                    'export_energy_today': lt_e,
                    'import_energy_lifetime': 840.0,
                    'export_energy_lifetime': 1559000.0 + lt_e,
                    'quality': DataQuality.VALID
                }
            )

    # Seed sample realistic alarms
    AlarmEvent.objects.get_or_create(
        device=inverters[2],
        code="W021",
        defaults={
            'description': "String 14 High Impedance / Shadow Warning",
            'severity': AlarmSeverity.WARNING,
            'fault_text': "Current deviation on String 14 exceeded 15% threshold.",
            'start_time': now - timedelta(hours=3),
            'is_active': True,
            'is_acknowledged': False
        }
    )
    AlarmEvent.objects.get_or_create(
        device=inverters[6],
        code="I012",
        defaults={
            'description': "Grid Frequency Transient Spike",
            'severity': AlarmSeverity.INFO,
            'fault_text': "Self-recovered momentary grid frequency fluctuation 50.35 Hz.",
            'start_time': now - timedelta(hours=6),
            'end_time': now - timedelta(hours=5, minutes=58),
            'is_active': False,
            'is_acknowledged': True
        }
    )
