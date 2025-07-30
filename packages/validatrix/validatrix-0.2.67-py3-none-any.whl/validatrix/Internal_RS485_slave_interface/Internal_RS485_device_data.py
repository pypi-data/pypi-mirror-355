
#region WF_chiller_data

WF_chiller_fault_list=["chiller_liquid_line_probe_fail",
                    "chiller_aft_probe_fail",
                    "chiller_room_temp_probe_ht_fault",
                    "chiller_room_temp_probe_lt_fault",
                    "chiller_pump_overload_fault",
                    "chiller_compressor_overload_fault",
                    "chiller_hp_fault",
                    "chiller_lp_fault",                    
                    "chiller_low_liquid_level_fault",                    
                    "chiller_high_temp_fault",
                    "chiller_aft_fault"]


WF_chiller_data={    
    "chiller_liquid_temp":10,
    "chiller_aft_temp":20,

    "chiller_room_temp_probe_fail":0,
    "chiller_aft_probe_fail":0,
    "chiller_room_temp_probe_ht_fault":0,
    "chiller_room_temp_probe_lt_fault":0,
    
    "chiller_pump_overload_fault":0,
    "chiller_spp_fault":0,
    "chiller_compressor_overload_fault":0,
    "chiller_hp_fault":0,
    "chiller_lp_fault":0,

    "chiller_low_liquid_level_fault":0,
    "chiller_liquid_line_high_temp_fault":0,    
    "chiller_high_temp_fault":0,
    "chiller_aft_fault":0,
    
    "chiller_compressor_on":0,
    "chiller_pump_on":0,
    "chiller_sv_on":0,
    "chiller_alarm_on":0,

    "chiller_set_high_set":40,
    "chiller_set_low_set":9,
    "chiller_set_set_point":10,
    "chiller_set_differential":2,
    "chiller_set_high_temp_alarm":50,
    "chiller_set_low_temp_alarm":8,
    "chiller_set_aft_set_temp":4,
    "chiller_set_aft_differential":2,
    "chiller_remote_start":1,

    }

WF_chiller_data_base={
    
    "chiller_liquid_temp":10,
    "chiller_aft_temp":20,

    "chiller_room_temp_probe_fail":0,
    "chiller_aft_probe_fail":0,
    "chiller_room_temp_probe_ht_fault":0,
    "chiller_room_temp_probe_lt_fault":0,
    
    "chiller_pump_overload_fault":0,
    "chiller_spp_fault":0,
    "chiller_compressor_overload_fault":0,
    "chiller_hp_fault":0,
    "chiller_lp_fault":0,

    "chiller_low_liquid_level_fault":0,
    "chiller_liquid_line_high_temp_fault":0,
    "chiller_high_temp_fault":0,
    "chiller_aft_fault":0,
    
    "chiller_compressor_on":0,
    "chiller_pump_on":0,
    "chiller_sv_on":0,
    "chiller_alarm_on":0,

    "chiller_set_high_set":40,
    "chiller_set_low_set":9,
    "chiller_set_set_point":10,
    "chiller_set_differential":2,
    "chiller_set_high_temp_alarm":50,
    "chiller_set_low_temp_alarm":8,
    "chiller_set_aft_set_temp":4,
    "chiller_set_aft_differential":2,
    "chiller_remote_start":1,

    }

#endregion WF_chiller_data

#region WF_heater_data

WF_heater_data={
    'heater_tank_temperature':25,

    'heater_relay_sts_compressor':1,
    'heater_relay_sts_alarm':1,

    'heater_fault_sts_probe_fail_low':0,
    'heater_fault_sts_probe_fail_high':0,
    'heater_fault_sts_ht':0,
    'heater_fault_sts_lt':0,
    'heater_fault_water_level_low':0,
    'heater_fault':0,

    'heater_run_hours':20,
    "heater_set_point":50,
    
    "heater_high_temp_limit":55,
    "heater_high_temp_alarm_diff":2,
    "heater_low_temp_limit":40,
    "heater_low_temp_alarm_diff":2,
    
    "heater_max_set_point_limit":52,
    "heater_min_set_point_limit":42,
    "heater_relay_on_differential":5,
    "heater_probe_calibration":0,    
    "heater_relay_min_on_time":0,
    "heater_fault_condition_when_probe_fail":0
    }


WF_heater_base_data={
    'heater_tank_temperature':25,

    'heater_relay_sts_compressor':1,
    'heater_relay_sts_alarm':1,

    'heater_fault_sts_probe_fail_low':0,
    'heater_fault_sts_probe_fail_high':0,
    'heater_fault_sts_ht':0,
    'heater_fault_sts_lt':0,
    'heater_fault_water_level_low':0,
    'heater_fault':0,

    'heater_run_hours':20,
    "heater_set_point":50,
    "heater_high_temp_limit":55,
    "heater_high_temp_alarm_diff":2,
    "heater_low_temp_limit":40,
    "heater_low_temp_alarm_diff":2,
    
    "heater_max_set_point_limit":52,
    "heater_min_set_point_limit":42,
    "heater_relay_on_differential":5,
    "heater_probe_calibration":0,    
    "heater_relay_min_on_time":0,
    "heater_fault_condition_when_probe_fail":0
    }

WF_heater_registers={    
    'heater_tank_temperature':6,
    'relay_status':11,
    'fault_status':12,

    'heater_run_hours':14,
    "heater_set_point":31,
    "heater_high_temp_limit":33,
    "heater_high_temp_alarm_diff":34,
    "heater_low_temp_limit":35,
    "heater_low_temp_alarm_diff":36,
    
    "heater_max_set_point_limit":37,
    "heater_min_set_point_limit":38,
    "heater_relay_on_differential":39,
    "heater_probe_calibration":40,    
    "heater_relay_min_on_time":42,
    "heater_fault_condition_when_probe_fail":43    
    }



#endregion WF_heater_data

#region LT_AC_EM_data

### byte 1 controls the data after decimal
### byte 2 controls that data before decimal point

LT_AC_EM_data_dict={
        'em_watts_total':0,
        'em_watts_r_phase':0,
        'em_watts_y_phase':0,
        'em_watts_b_phase':0,

        'em_power_factor_avg':0.8,
        'em_power_factor_r_phase':0.7,
        'em_power_factor_y_phase':0.5,
        'em_power_factor_b_phase':0.9,

        'em_apparent_power_total':0,
        'em_apparent_power_r_phase':0,
        'em_apparent_power_y_phase':0,
        'em_apparent_power_b_phase':0,

        'em_voltage_ll_avg':440,
        'em_voltage_ry_phase':440,
        'em_voltage_yb_phase':440,
        'em_voltage_br_phase':440,

        'em_voltage_ln_avg':220.6,
        'em_voltage_r_phase':250.5,
        'em_voltage_y_phase':210.4,
        'em_voltage_b_phase':234.8,

        'em_current_total':0,
        'em_current_r_phase':0,
        'em_current_y_phase':0,
        'em_current_b_phase':0,

        'em_frequency':0,
        'em_k_watt_hour':0,
        'em_voltage_ampere_hour':0,

}


LT_AC_EM_data_dict_base={
        'em_watts_total':0,
        'em_watts_r_phase':0,
        'em_watts_y_phase':0,
        'em_watts_b_phase':0,

        'em_power_factor_avg':0.8,
        'em_power_factor_r_phase':0.7,
        'em_power_factor_y_phase':0.5,
        'em_power_factor_b_phase':0.9,

        'em_apparent_power_total':0,
        'em_apparent_power_r_phase':0,
        'em_apparent_power_y_phase':0,
        'em_apparent_power_b_phase':0,

        'em_voltage_ll_avg':440,
        'em_voltage_ry_phase':440,
        'em_voltage_yb_phase':440,
        'em_voltage_br_phase':440,

        'em_voltage_ln_avg':220.6,
        'em_voltage_r_phase':250.5,
        'em_voltage_y_phase':210.4,
        'em_voltage_b_phase':234.8,

        'em_current_total':0,
        'em_current_r_phase':0,
        'em_current_y_phase':0,
        'em_current_b_phase':0,

        'em_frequency':0,
        'em_k_watt_hour':0,
        'em_voltage_ampere_hour':0,

}

LT_AC_EM_registers_dict={
            'em_watts_total':[101,2,'<','<','Float32'],
            'em_watts_r_phase':[103,2,'<','<','Float32'],
            'em_watts_y_phase':[105,2,'<','<','Float32'],
            'em_watts_b_phase':[107,2,'<','<','Float32'],

            'em_power_factor_avg':[117,2,'<','<','Float32'],
            'em_power_factor_r_phase':[119,2,'<','<','Float32'],
            'em_power_factor_y_phase':[121,2,'<','<','Float32'],
            'em_power_factor_b_phase':[123,2,'<','<','Float32'],

            'em_apparent_power_total':[125,2,'<','<','Float32'],
            'em_apparent_power_r_phase':[127,2,'<','<','Float32'],
            'em_apparent_power_y_phase':[129,2,'<','<','Float32'],
            'em_apparent_power_b_phase':[131,2,'<','<','Float32'],

            'em_voltage_ll_avg':[133,2,'<','<','Float32'],
            'em_voltage_ry_phase':[135,2,'<','<','Float32'],
            'em_voltage_yb_phase':[137,2,'<','<','Float32'],
            'em_voltage_br_phase':[139,2,'<','<','Float32'],

            'em_voltage_ln_avg':[141,2,'<','<','Float32'],
            'em_voltage_r_phase':[143,2,'<','<','Float32'],
            'em_voltage_y_phase':[145,2,'<','<','Float32'],
            'em_voltage_b_phase':[147,2,'<','<','Float32'],

            'em_current_total':[149,2,'<','<','Float32'],
            'em_current_r_phase':[151,2,'<','<','Float32'],
            'em_current_y_phase':[153,2,'<','<','Float32'],
            'em_current_b_phase':[155,2,'<','<','Float32'],

            'em_frequency':[157,2,'<','<','Float32'],
            'em_k_watt_hour':[159,2,'<','<','Float32'],
            'em_voltage_ampere_hour':[161,2,'<','<','Float32']

           
        }

#endregion LT_AC_EM_data

#region A9MEM3250_AC_EM_data

####[start_address, number_of_words, byte_order, data_order, data_type, unit, gain_factor]

A9MEM3250_AC_EM_registers_dict={
        'phase_1_current':[2999,2,'<','<','Float32','A',1],
        'phase_2_current':[3001,2,'<','<','Float32','A',1],
        'phase_3_current':[3003,2,'<','<','Float32','A',1],
        'Current_Avg':[3009,2,'<','<','Float32','A',1],

        'Voltage_L1_L2':[3019,2,'<','<','Float32','V',1],
        'Voltage_L2_L3':[3021,2,'<','<','Float32','V',1],
        'Voltage_L3_L1':[3023,2,'<','<','Float32','V',1],
        'Voltage_L_L_Avg':[3025,2,'<','<','Float32','V',1],
        'Voltage_L1_N':[3027,2,'<','<','Float32','V',1],
        'Voltage_L2_N':[3029,2,'<','<','Float32','V',1],
        'Voltage_L3_N':[3031,2,'<','<','Float32','V',1],
        'Voltage_L_N_Avg':[3035,2,'<','<','Float32','V',1],

        'Active_Power_Phase_1':[3053,2,'<','<','Float32','kW',1],
        'Active_Power_Phase_2':[3055,2,'<','<','Float32','kW',1],
        'Active_Power_Phase_3':[3057,2,'<','<','Float32','kW',1],
        'Total_Active_Power':[3059,2,'<','<','Float32','kW',1],

        'Total_Power_Factor':[3083,2,'<','<','Float32','',1],
        'Frequency':[3109,2,'<','<','Float32','Hz',1],

        'Total_Active_Energy_Import':[3203,4,'<','<','Int64','Wh',1],
        'Partial_Active_Energy_Import':[3255,4,'<','<','Int64','Wh',1],
        'Active_Energy_Import_Phase_1':[3517,4,'<','<','Int64','Wh',1],
        'Active_Energy_Import_Phase_2':[3521,4,'<','<','Int64','Wh',1],
        'Active_Energy_Import_Phase_3':[3525,4,'<','<','Int64','Wh',1],

        'Total_Active_Energy_Import_float':[5099,2,'<','<','Float32','kWh',1],
        'Partial_Active_Energy_Import_float':[5107,2,'<','<','Float32','kWh',1],
        'Active_Energy_Import_Phase_1_float':[5111,2,'<','<','Float32','kWh',1],
        'Active_Energy_Import_Phase_2_float':[5113,2,'<','<','Float32','kWh',1],
        'Active_Energy_Import_Phase_3_float':[5115,2,'<','<','Float32','kWh',1],

        
}

A9MEM3250_AC_EM_data_dict={
        'phase_1_current':50,
        'phase_2_current':60,
        'phase_3_current':70,
        'Current_Avg':80,

        'Voltage_L1_L2':880.6,
        'Voltage_L2_L3':440,
        'Voltage_L3_L1':440,
        'Voltage_L_L_Avg':440,
        'Voltage_L1_N':220,
        'Voltage_L2_N':220,
        'Voltage_L3_N':220,
        'Voltage_L_N_Avg':220,

        'Active_Power_Phase_1':11,
        'Active_Power_Phase_2':11,
        'Active_Power_Phase_3':11,
        'Total_Active_Power':33,

        'Total_Power_Factor':1,
        'Frequency':50,

        'Total_Active_Energy_Import':10000,
        'Partial_Active_Energy_Import':20000,
        'Active_Energy_Import_Phase_1':30000,
        'Active_Energy_Import_Phase_2':40000,
        'Active_Energy_Import_Phase_3':50000,

        'Total_Active_Energy_Import_float':33,
        'Partial_Active_Energy_Import_float':30,
        'Active_Energy_Import_Phase_1_float':11,
        'Active_Energy_Import_Phase_2_float':11,
        'Active_Energy_Import_Phase_3_float':11,
}

A9MEM3250_AC_EM_data_base_dict={
        'phase_1_current':50,
        'phase_2_current':60,
        'phase_3_current':70,
        'Current_Avg':80,

        'Voltage_L1_L2':880.6,
        'Voltage_L2_L3':440,
        'Voltage_L3_L1':440,
        'Voltage_L_L_Avg':440,
        'Voltage_L1_N':220,
        'Voltage_L2_N':220,
        'Voltage_L3_N':220,
        'Voltage_L_N_Avg':220,

        'Active_Power_Phase_1':11,
        'Active_Power_Phase_2':11,
        'Active_Power_Phase_3':11,
        'Total_Active_Power':33,

        'Total_Power_Factor':1,
        'Frequency':50,

        'Total_Active_Energy_Import':10000,
        'Partial_Active_Energy_Import':20000,
        'Active_Energy_Import_Phase_1':30000,
        'Active_Energy_Import_Phase_2':40000,
        'Active_Energy_Import_Phase_3':50000,

        'Total_Active_Energy_Import_float':33,
        'Partial_Active_Energy_Import_float':30,
        'Active_Energy_Import_Phase_1_float':11,
        'Active_Energy_Import_Phase_2_float':11,
        'Active_Energy_Import_Phase_3_float':11,
}

#endregion A9MEM3250_AC_EM_data

#region PD195Z-CD31F_DC_EM_data


####[start_address, number_of_words, byte_order, data_order, data_type, unit, gain_factor]

PD195Z_CD31F_DC_EM_registers_dict={
        'Circuit_1_voltage':[6,2,'>','>','Int32','V',10],
        'Circuit_1_current':[8,2,'>','>','Int32','A',10],
        'Circuit_1_power':[10,2,'>','>','Int32','kW',10],
        'Circuit_1_positive_energy':[12,4,'>','>','Int64','wh',0.1],
        'Circuit_1_negetive_energy':[16,4,'>','>','Int64','wh',0.1],

        'Circuit_2_voltage':[20,2,'>','>','Int32','V',10],
        'Circuit_2_current':[22,2,'>','>','Int32','A',10],
        'Circuit_2_power':[24,2,'>','>','Int32','kW',10],
        'Circuit_2_positive_energy':[26,4,'>','>','Int64','wh',0.1],
        'Circuit_2_negetive_energy':[30,4,'>','>','Int64','wh',0.1],
        
}

PD195Z_CD31F_DC_EM_data_dict={
        'Circuit_1_voltage':50,
        'Circuit_1_current':10,
        'Circuit_1_power':0.5,
        'Circuit_1_positive_energy':500,
        'Circuit_1_negetive_energy':500,

        'Circuit_2_voltage':50,
        'Circuit_2_current':10,
        'Circuit_2_power':0.5,
        'Circuit_2_positive_energy':500,
        'Circuit_2_negetive_energy':500,
}

PD195Z_CD31F_DC_EM_data_base_dict={
        'Circuit_1_voltage':50,
        'Circuit_1_current':10,
        'Circuit_1_power':0.5,
        'Circuit_1_positive_energy':500,
        'Circuit_1_negetive_energy':500,

        'Circuit_2_voltage':50,
        'Circuit_2_current':10,
        'Circuit_2_power':0.5,
        'Circuit_2_positive_energy':500,
        'Circuit_2_negetive_energy':500,
}

#endregion PD195Z-CD31F_DC_EM_data