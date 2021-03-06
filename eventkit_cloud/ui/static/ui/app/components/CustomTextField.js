import React, { Component, PropTypes } from 'react';
import { TextField } from 'material-ui';
import * as ReactDOM from 'react-dom';

export class CustomTextField extends Component {
    constructor(props) {
        super(props);
        this.onChange = this.onChange.bind(this);
        this.onFocus = this.onFocus.bind(this);
        this.onBlur = this.onBlur.bind(this);
        this.state = {
            charsRemaining: this.props.maxLength,
            focused: false,
        };

        this.styles = {
            charsRemaining: {
                position: 'absolute',
                bottom: '4px',
                right: '16px',
                transform: 'translateY(-50%)',
                fontWeight: 'bold',
            },
        };
    }

    onChange(e, val) {
        if (this.props.onChange) {
            this.props.onChange(e, val);
        }

        this.setState({ charsRemaining: this.props.maxLength - e.target.value.length });
    }

    onFocus(e) {
        if (this.props.onFocus) {
            this.props.onFocus(e);
        }

        this.setState({ focused: true });
    }

    onBlur(e) {
        if (this.props.onBlur) {
            this.props.onBlur(e);
        }

        this.setState({ focused: false });
    }

    render() {
        const {
            showRemaining,
            onChange,
            onFocus,
            onBlur,
            ...rest
        } = this.props;

        const charsRemainingColor = (this.state.charsRemaining > 10) ? '#B4B7B8' : '#CE4427';

        return (
            <div style={{ position: 'relative' }}>
                <TextField
                    className="qa-CustomTextField-TextField"
                    id="custom-text-field"
                    ref={(textField) => {
                        if (!textField) {
                            return;
                        }

                        if (this.props.maxLength && this.props.showRemaining) {
                            ReactDOM.findDOMNode(textField).style.paddingRight = '55px';
                        }
                    }}
                    onChange={this.onChange}
                    onFocus={this.onFocus}
                    onBlur={this.onBlur}
                    {...rest}
                />
                {(this.props.maxLength && this.props.showRemaining && this.state.focused) ?
                    <div
                        className="qa-CustomTextField-div-charsRemaining"
                        style={{ ...this.styles.charsRemaining, color: charsRemainingColor }}
                    >
                        {this.state.charsRemaining}
                    </div>
                    :
                    null
                }
            </div>
        );
    }
}

CustomTextField.propTypes = {
    showRemaining: PropTypes.bool,
    maxLength: PropTypes.number,
    onChange: PropTypes.func,
    onFocus: PropTypes.func,
    onBlur: PropTypes.func,
};

CustomTextField.defaultProps = {
    showRemaining: true,
    maxLength: 100,
    onChange: undefined,
    onFocus: undefined,
    onBlur: undefined,
};

export default CustomTextField;
