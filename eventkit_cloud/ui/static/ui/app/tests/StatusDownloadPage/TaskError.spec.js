import React from 'react';
import sinon from 'sinon';
import { mount, shallow } from 'enzyme';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import Divider from 'material-ui/Divider';
import Warning from 'material-ui/svg-icons/alert/warning';
import TaskError from '../../components/StatusDownloadPage/TaskError';
import BaseDialog from '../../components/Dialog/BaseDialog';

describe('TaskError component', () => {
    const getProps = () => (
        {
            task: {
                uid: '1975da4d-9580-4fa8-8a4b-c1ef6e2f7553',
                url: 'http://cloud.eventkit.test/api/tasks/1975da4d-9580-4fa8-8a4b-c1ef6e2f7553',
                name: 'OSM Data (.gpkg)',
                status: 'CANCELED',
                progress: 0,
                estimated_finish: null,
                started_at: null,
                finished_at: null,
                duration: null,
                result: null,
                errors: [
                    {
                        exception: 'OpenStreetMap Data (Themes) was canceled by admin.',
                    },
                ],
                display: true,
            },
        }
    );

    const muiTheme = getMuiTheme();

    const getWrapper = props => (
        mount(<TaskError {...props} />, {
            context: { muiTheme },
            childContextTypes: {
                muiTheme: React.PropTypes.object,
            },
        })
    );

    it('should render UI elements', () => {
        const props = getProps();
        const wrapper = getWrapper(props);
        expect(wrapper.find('span').find('a').text()).toEqual('ERROR');
        expect(wrapper.find(BaseDialog)).toHaveLength(1);
    });

    it('handleTaskErrorOpen should set task error dialog to open', () => {
        const props = getProps();
        const stateSpy = sinon.spy(TaskError.prototype, 'setState');
        const wrapper = shallow(<TaskError {...props} />);
        expect(stateSpy.called).toBe(false);
        wrapper.instance().handleTaskErrorOpen();
        expect(stateSpy.calledOnce).toBe(true);
        expect(stateSpy.calledWith({ taskErrorDialogOpen: true })).toBe(true);
        expect(wrapper.find(Warning)).toHaveLength(1);
        expect(wrapper.find(Divider)).toHaveLength(1);
        expect(wrapper.find('.qa-TaskError-div-errorData').childAt(1).text()).toEqual(props.task.errors[0].exception);
        stateSpy.restore();
        stateSpy.restore();
    });

    it('handleTaskErrorClose should set task error dialog to close', () => {
        const props = getProps();
        const stateSpy = sinon.spy(TaskError.prototype, 'setState');
        const wrapper = shallow(<TaskError {...props} />);
        expect(stateSpy.called).toBe(false);
        wrapper.instance().handleTaskErrorClose();
        expect(stateSpy.calledOnce).toBe(true);
        expect(stateSpy.calledWith({ taskErrorDialogOpen: false })).toBe(true);
        stateSpy.restore();
    });

    it('should call handleTaskErrorOpen when the error link is clicked. ', () => {
        const props = getProps();
        const stateSpy = sinon.spy(TaskError.prototype, 'setState');
        const errorSpy = sinon.spy(TaskError.prototype, 'handleTaskErrorOpen');
        const wrapper = getWrapper(props);
        expect(errorSpy.notCalled).toBe(true);
        wrapper.find('a').simulate('click');
        expect(errorSpy.calledOnce).toBe(true);
        expect(stateSpy.calledWith({ taskErrorDialogOpen: true })).toBe(true);
        stateSpy.restore();
        errorSpy.restore();
    });
});
