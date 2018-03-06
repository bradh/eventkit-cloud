import React from 'react';
import PropTypes from 'prop-types';
import {mount} from 'enzyme';
import Loading from '../../components/auth/Loading';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import CircularProgress from 'material-ui/CircularProgress';

describe('Loading component', () => {
    const muiTheme = getMuiTheme();
    it('should render basic elemets', () => {
        const wrapper = mount(Loading(), {
            context: {muiTheme},
            childContextTypes: {muiTheme: PropTypes.object}
        });
        expect(wrapper.find(CircularProgress)).toHaveLength(1);
    });
});
