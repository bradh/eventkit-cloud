
import * as types from '../actions/actionTypes';
import initialState from './initialState';

export function exportJobsReducer(state = initialState.jobs, action) {
    switch(action.type) {
        case types.LOAD_JOBS_SUCCESS:
            return action.jobs;
        default:
            return state;
    }
}

export function exportModeReducer(state = initialState.mode, action) {
    switch(action.type) {
        case types.SET_MODE:
            return action.mode;
        default:
            return state;
    }
}

export function exportBboxReducer(state = initialState.bbox, action) {
    switch(action.type) {
        case types.UPDATE_BBOX:
            return action.bbox;
        default:
            return state;
    }
}