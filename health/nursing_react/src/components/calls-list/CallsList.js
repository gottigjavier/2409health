import {useContext, useEffect, useState} from 'react';
import './calls-list.css';
import Call from './call/Call';
import {callsManager} from '../../services/calls-socket';
import AppContext from '../../context/appContext';
import sounds from '../../media/call-tone.mp3';
import {Howl} from 'howler';




export default function CallsList(props){
    const [appState, setAppState] = useContext(AppContext); // looks like hook?
    const [listCallsLen, setListCallsLen] = useState(appState.calls.length);
    const places = props.places;
    let AudioContext = window.AudioContext || window.webkitAudioContext;
    let audioCtx = new AudioContext();


    // Setup the new Howl.
    const sounder = new Howl({
        src: [sounds]
    });
        
    useEffect(() => {
        callsManager({handleCall})
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        return(() => {
            audioCtx.suspend()
        })
    }, [])

    useEffect(() => {
        setListCallsLen(appState.calls.length)
    }, [appState.calls.length])

    const handleCall = async msg => {
        if (msg.state){
            if(msg.call){
                await setAppState(msg.call)
                setListCallsLen(msg.call.calls.length)
                sounder.play() // First alert. Next handled by component "Call"
            } else {
                console.log('Repeated Call or Unoccupied Bed')
            }
        } else {
            setAppState(msg.call)
            setListCallsLen(msg.call.calls.length)
            answeredCall(msg);
        }
    }

// ------------------- Answered Call ----------------------------------
    const answeredCall = call =>{
        call.bed = call.bed.split(",")[0];
        const callsList = call.call.calls
        const BEDS = places.numBeds;
        let saveCallsList = [];
        if (callsList.length > 0){
            for (let bed=1; bed<=BEDS; bed++){
                let answCall = `${call.bed},${bed}`
                callsList.map(elem => {
                    if(elem.bed === answCall && elem.state === 'active'){
                        elem.state = 'answered'
                        elem.response_time = new Date()
                        saveCallsList.push(elem)
                    }
                    return null
                })
            }
            saveAnsweredCall(saveCallsList)
            }
        else {
            console.log('No calls to answered')
        }
    }

    const saveAnsweredCall = async (saveCallsList) => {
        if (saveCallsList.length > 0) {
            import('../../services/api').then(({ authFetch, fetchLoad }) => {
                const promises = saveCallsList.map(elem => {
                    // Prefer explicit id if provided
                    const id = elem.id || elem.pk || elem.call_id;
                    if (id) return authFetch(`/calls/${id}/answer`, { method: 'POST' });
                    // fallback: find call by bed in current appState.calls
                    const match = (appState.calls || []).find(c => c.bed === elem.bed && c.state === 'active');
                    if (match) return authFetch(`/calls/${match.id}/answer`, { method: 'POST' });
                    return Promise.resolve();
                });
                Promise.all(promises)
                .then(() => fetchLoad())
                .then(data => setAppState(data))
                .catch(error => console.log(`An ERROR occurred while saving the Answered Calls: ${error}`));
            })
        }
    }
    // ---------------------- end answered call --------------------------

    return (
        <>
            <div className="call-title row justify-content-center clshdw rounded my-2">
                <p className="call-title-text">Llamadas</p>
            </div>
            <div className="calls-col">
            { 
            listCallsLen > 0 &&
                appState.calls.map( (call, index) =>  {
                    return (
                    <Call 
                        key = {`${call.bed},${index}`}
                        call = {call}
                        callBedAndIndex = {`${call.bed},${index}`} 
                    />
                    )
                })
            }
            </div>
        </>
    )
}
