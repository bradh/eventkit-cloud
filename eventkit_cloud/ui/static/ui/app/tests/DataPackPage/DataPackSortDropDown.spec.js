import React from 'react';
import PropTypes from 'prop-types';
import sinon from 'sinon';
import { mount } from 'enzyme';
import DropDownMenu from 'material-ui/DropDownMenu';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import DataPackSortDropDown from '../../components/DataPackPage/DataPackSortDropDown';

describe('DataPackSortDropDown component', () => {
    const muiTheme = getMuiTheme();
    const getProps = () => (
        {
            handleChange: () => {},
            value: '-started_at',
        }
    );

    const getWrapper = props => (
        mount(<DataPackSortDropDown {...props} />, {
            context: { muiTheme },
            childContextTypes: { muiTheme: PropTypes.object },
        })
    );

    it('should render a dropdown menu', () => {
        const props = getProps();
        const wrapper = getWrapper(props);
        expect(wrapper.find(DropDownMenu)).toHaveLength(1);
    });

    it('should render with text "Newest"', () => {
        const props = getProps();
        const wrapper = getWrapper(props);
        expect(wrapper.text()).toEqual('Newest');
    });

    it('should render with text "Oldest"', () => {
        const props = getProps();
        props.value = 'started_at';
        const wrapper = getWrapper(props);
        expect(wrapper.text()).toEqual('Oldest ');
    });

    it('should render with text "Name (A-Z)"', () => {
        const props = getProps();
        props.value = 'job__name';
        const wrapper = getWrapper(props);
        expect(wrapper.text()).toEqual('Name (A-Z)');
    });

    it('should render with text "Name (Z-A)"', () => {
        const props = getProps();
        props.value = '-job__name';
        const wrapper = getWrapper(props);
        expect(wrapper.text()).toEqual('Name (Z-A)');
    });

    it('should have the correct menu item labels', () => {
        const props = getProps();
        const wrapper = getWrapper(props);
        expect(wrapper.find(DropDownMenu)).toHaveLength(1);
        expect(wrapper.find(DropDownMenu).props().children[0].props.primaryText).toEqual('Featured');
        expect(wrapper.find(DropDownMenu).props().children[1].props.primaryText).toEqual('Newest');
        expect(wrapper.find(DropDownMenu).props().children[2].props.primaryText).toEqual('Oldest ');
        expect(wrapper.find(DropDownMenu).props().children[3].props.primaryText).toEqual('Name (A-Z)');
        expect(wrapper.find(DropDownMenu).props().children[4].props.primaryText).toEqual('Name (Z-A)');
    });
    
    it('should call onChange when an item is selected', () => {
        const props = getProps();
        props.handleChange = sinon.spy();
        const wrapper = getWrapper(props);
        const e = {};
        wrapper.find(DropDownMenu).props().onChange(e, 2, 'started_at');
        expect(props.handleChange.calledOnce).toBe(true);
        expect(props.handleChange.calledWith(e, 2, 'started_at')).toEqual(true);
    });

    it('should adjust styles for small screens', () => {
        window.resizeTo(1000, 900);
        expect(window.innerWidth).toBe(1000);
        const props = getProps();
        const wrapper = mount(<DataPackSortDropDown {...props} />, {
            context: { muiTheme },
            childContextTypes: { muiTheme: PropTypes.object },
        });
        expect(wrapper.find(DropDownMenu).props().labelStyle.fontSize).toEqual('14px');

        window.resizeTo(500, 600);
        expect(window.innerWidth).toBe(500);
        wrapper.instance().forceUpdate();
        wrapper.update();
        expect(wrapper.find(DropDownMenu).props().labelStyle.fontSize).toEqual('12px');
    });
});
