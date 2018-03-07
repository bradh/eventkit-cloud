import React from 'react';
import PropTypes from 'prop-types';
import sinon from 'sinon';
import { mount } from 'enzyme';
import DropDownMenu from 'material-ui/DropDownMenu';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import DataPackOwnerSort from '../../components/DataPackPage/DataPackOwnerSort';

describe('DataPackOwnerSort component', () => {
    const muiTheme = getMuiTheme();    
    const getProps = () => (
        {
            value: '',
            handleChange: () => {},
            owner: 'test_user',
        }
    );

    const getWrapper = props => (
        mount(<DataPackOwnerSort {...props} />, {
            context: { muiTheme },
            childContextTypes: { muiTheme: PropTypes.object },
        })
    );

    it('should render a dropdown menu', () => {
        const props = getProps();
        const wrapper = getWrapper(props);
        expect(wrapper.find(DropDownMenu)).toHaveLength(1);
    });

    it('should render with text "All DataPacks"', () => {
        const props = getProps();
        const wrapper = getWrapper(props);
        expect(wrapper.text()).toEqual('All DataPacks');
    });

    it('should render with text "My DataPacks"', () => {
        const props = getProps();
        props.value = 'test_user';
        const wrapper = getWrapper(props);
        expect(wrapper.text()).toEqual('My DataPacks');
    });

    it('should display the right default selected value text', () => {
        const props = getProps();
        const wrapper = getWrapper(props);
        expect(wrapper.find(DropDownMenu)).toHaveLength(1);
        expect(wrapper.find(DropDownMenu).text()).toEqual('All DataPacks');
    });

    it('should have the correct menu item labels', () => {
        const props = getProps();
        const wrapper = getWrapper(props);
        expect(wrapper.find(DropDownMenu)).toHaveLength(1);
        const { children } = wrapper.find(DropDownMenu).props();
        expect(children[0].props.primaryText).toEqual('All DataPacks');
        expect(children[1].props.primaryText).toEqual('My DataPacks');
    });

    it('should call onChange when an item is selected', () => {
        const props = getProps();
        props.handleChange = sinon.spy();
        const wrapper = getWrapper(props);
        const e = {};
        wrapper.find(DropDownMenu).props().onChange(e, 1, 'My DataPacks');
        expect(props.handleChange.calledOnce).toBe(true);
        expect(props.handleChange.calledWith(e, 1, 'My DataPacks'));
    });

    it('should render differently for small screens', () => {
        window.resizeTo(1000, 700);
        expect(window.innerWidth).toBe(1000);

        const props = getProps();
        const wrapper = getWrapper(props);
        expect(wrapper.find(DropDownMenu).props().labelStyle.fontSize).toEqual('14px');

        window.resizeTo(400, 500);
        wrapper.instance().forceUpdate();
        wrapper.update();
        expect(window.innerWidth).toBe(400);
        expect(wrapper.find(DropDownMenu).props().labelStyle.fontSize).toEqual('12px');
    });
});
