import React, { Component } from 'react';
import PropTypes from 'prop-types';

export class InfoParagraph extends Component {

    constructor(props) {
        super(props);
    };

    render() {
        if (!this.props.header || !this.props.body) {
            return null;
        }

        return (
            <div className={'qa-InfoParagraph-header'}>
                <h4 style={this.props.headerStyle}><strong>{this.props.header}</strong></h4>
                <div id={this.props.header} style={this.props.bodyStyle} className={'qa-InfoParagraph-body'}>
                    {this.props.body}
                </div>
            </div>
        )
    };
};

InfoParagraph.propTypes = {
    header: PropTypes.string.isRequired,
    body: PropTypes.string.isRequired,
    headerStyle: PropTypes.object,
    bodyStyle: PropTypes.object,
}

export default InfoParagraph;
