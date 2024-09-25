

def serial_beds(beds):
    beds_list =[]
    if beds:
        for bed in beds:
            pk_id = bed.id
            bed_id = bed.id_bed
            bed_active = bed.active
            bed_occupied_time = bed.occupied_time.isoformat()
            bed_planed_vacate = bed.planed_vacate.isoformat()
            bed_state = bed.bed_state
            patient = bed.bed_patient.name
            patient_pk = bed.bed_patient.id
            patient_ssn = bed.bed_patient.social_security_number
            image = bed.bed_patient.image.name
            diagnosis = bed.bed_patient.short_diagnosis
            done_by = bed.action_done_by
            bed_dict = {
                'id': pk_id,
                'bed_id': bed_id,
                'bed_active': bed_active,
                'bed_occupied_time': bed_occupied_time,
                'bed_planed_vacate': bed_planed_vacate,
                'bed_state': bed_state,
                'patient': patient,
                'patient_id': patient_pk,
                'patient_security_number': patient_ssn,
                'image': image,
                'diagnosis': diagnosis,
                'action_done_by': done_by
            }
            beds_list.append(bed_dict)
    else:
        pass
    return beds_list