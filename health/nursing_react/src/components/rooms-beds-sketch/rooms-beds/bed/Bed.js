import React, { useContext, useEffect, useState } from 'react';
import './bed.css';
import AppContext from '../../../../context/appContext'
import BedModal from './bed-modal/BedModal'
import bedAvatar from '../../../../media/bed-solid.svg'


function Bed (props){
    
    const [appState, setAppState] = useContext(AppContext);
        
    const room = props.room;
    const bed = props.bed;
    const [show, setShow]= useState(false)
    const [currentBed, setCurrentBed] = useState({})

    const freeBed = {
        id : '',
        bed_id : room + ',' + bed,
        diagnosis : 'No Diagnosis',
        bed_state : 'free',
        bed_active : false,
        action_done_by : 'Anónimo',
        image : '',
        patient : 'No Name'
    }


    const toBedState = () => {
        const id_bed = room + ',' + bed;
        appState.beds.map( e => {
            if (id_bed === e.bed_id) {
                setCurrentBed(e)
            }
        })
    }

    useEffect(() => {
        setCurrentBed(freeBed)
    }, [])

    useEffect(() => {
        toBedState()
    }, [appState.beds])

    // Ensure the bed classes update when appState changes (WS driven updates)
    useEffect(() => {
        // force re-render by updating currentBed from appState on any appState change
        toBedState()
    }, [appState])

    // Log bed state transitions to help debugging WS ordering issues
    useEffect(() => {
        const bedId = room + ',' + bed;
        const callsLen = (appState.calls || []).filter(c => c.bed === bedId).length;
        const tasksLen = (appState.tasks || []).filter(t => t.bed === bedId).length;
        console.debug('Bed render', { bed: bedId, currentBed: currentBed.bed_state, bed_active: currentBed.bed_active, calls: callsLen, tasks: tasksLen });
    }, [currentBed, appState.calls, appState.tasks]);

    // Show Modal ---------------------------
    const showBedModal = () => {
        setShow(show => show = true);
    };
    
    const hideBedModal = () => {
        setShow(show => show = false);
    };
    
    // determine visual class based on calls and tasks (take precedence over bed_state)
    const bedIdStr = room + ',' + bed;
    const calls = appState.calls || [];
    const tasks = appState.tasks || [];
    const activeCall = (calls.find(c => c.bed === bedIdStr && c.state === 'active')) !== undefined;
    const answeredCall = (calls.find(c => c.bed === bedIdStr && c.state === 'answered')) !== undefined;
    const relevantTasks = tasks.filter(t => t.bed === bedIdStr && t.active);
    const hasPassedTask = relevantTasks.some(t => t.state === 'passed');
    const hasSoonTask = relevantTasks.some(t => t.state === 'soon');

    let visualState = currentBed.bed_state || 'free';

    if (!currentBed.bed_active) {
        visualState = 'free';
    } else if (activeCall) {
        if (hasPassedTask) visualState = 'call-task';
        else visualState = 'call';
    } else {
        if (hasPassedTask) visualState = 'task';
        else if (hasSoonTask) visualState = 'soon';
        else visualState = 'occupied';
    }

    // log the computed visual state for debugging
    useEffect(() => {
        console.debug('Bed visualState computed', { bed: bedIdStr, visualState });
    }, [visualState, bedIdStr]);

    return (       
        <>     
            <div className={`metal card bshdw rounded bed ${visualState}`} id= {'b-' + room + ',' + bed} 
                onClick={showBedModal} title={currentBed.patient}>
                <div className="bed-title text-center px-2">
                    {bed + ' '}
                </div>
                <h5 className="text-center px-2"> 
                    <img src={bedAvatar} alt="Bed" className='bed-avatar'></img>
                </h5> 
            </div>
            { show &&
                <BedModal
                show = {show}
                hideBedModal = {hideBedModal}
                currentBed = {currentBed}
                />
            }
        </>
    )
}

export default Bed;
