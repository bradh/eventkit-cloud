
import {combineReducers} from 'redux';
import jobs from './exportReducer';

const rootReducer = combineReducers({
    // short hand property names
    jobs
})

export default rootReducer;