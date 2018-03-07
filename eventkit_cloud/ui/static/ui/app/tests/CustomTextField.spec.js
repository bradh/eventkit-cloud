import React from 'react';
import PropTypes from 'prop-types';
import { mount } from 'enzyme';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import { TextField } from 'material-ui';
import CustomTextField from '../components/CustomTextField';

describe('CustomTextField component', () => {
    const muiTheme = getMuiTheme();

    it('should render a material-ui TextField component', () => {
        const wrapper = mount(<CustomTextField />, {
            context: { muiTheme },
            childContextTypes: { muiTheme: PropTypes.object },
        });
        expect(wrapper.find(TextField)).toHaveLength(1);
    });

    it('should show remaining characters when maxLength is present and input is focused', () => {
        const wrapper = mount(<CustomTextField maxLength={100} />, {
            context: { muiTheme },
            childContextTypes: { muiTheme: PropTypes.object },
        });
        let input = wrapper.find('input');
        let charsRemaining = wrapper.find('.qa-CustomTextField-div-charsRemaining');
        expect(charsRemaining).toHaveLength(0);
        input.simulate('focus');
        wrapper.update();
        charsRemaining = wrapper.find('.qa-CustomTextField-div-charsRemaining');
        expect(charsRemaining).toHaveLength(1);
        expect(charsRemaining.text()).toEqual('100');
        input = wrapper.find('input');
        input.simulate('change', { target: { value: 'abc' } });
        wrapper.update();
        charsRemaining = wrapper.find('.qa-CustomTextField-div-charsRemaining');
        expect(charsRemaining.text()).toEqual('97');
        input = wrapper.find('input');
        input.simulate('blur');
        charsRemaining = wrapper.find('.qa-CustomTextField-div-charsRemaining');
        expect(charsRemaining).toHaveLength(0);
    });

    it('should not show remaining characters when showRemaining is false', () => {
        const wrapper = mount(<CustomTextField maxLength={100} showRemaining={false} />, {
            context: { muiTheme },
            childContextTypes: { muiTheme: PropTypes.object },
        });
        const input = wrapper.find('input');
        let charsRemaining = wrapper.find('.qa-CustomTextField-div-charsRemaining');
        expect(charsRemaining).toHaveLength(0);
        input.simulate('focus');
        charsRemaining = wrapper.find('.qa-CustomTextField-div-charsRemaining');
        expect(charsRemaining).toHaveLength(0);
    });
});
