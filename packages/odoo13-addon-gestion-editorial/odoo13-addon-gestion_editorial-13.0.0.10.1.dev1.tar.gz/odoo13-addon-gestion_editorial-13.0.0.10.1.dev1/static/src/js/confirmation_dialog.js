odoo.define('gestion_editorial.ConfirmationDialog', function (require) {
    "use strict";
    
    var FormController = require('web.FormController');
    var Dialog = require('web.Dialog');
    var core = require('web.core');
    var _t = core._t;
    
    var _superSaveRecord = FormController.prototype.saveRecord;
    
    FormController.include({
        saveRecord: function () {
            var self = this;
            var record = this.model.get(this.handle);
            
            // Save normally if it's not a product - We can add other models in the future here
            if (this.modelName !== 'product.template') {
                return _superSaveRecord.call(this);
            }
            
            // RPC call to check conditions
            return this._rpc({
                model: this.modelName,
                method: 'check_save_conditions',    // This method must be available in the model 
                args: [record.data]
            }).then(function (conditions) {
                if (conditions && conditions.length > 0) {
                    // Show custom dialogs
                    return self._showCustomConfirmDialogs(conditions)
                        .then(function () {
                            // Confirmed response, so save
                            return _superSaveRecord.call(self);
                        })
                        .catch(function () {
                            // Error, so cancel
                            return Promise.reject(new Error('SaveCancelled'));
                        });
                } else {
                    // If no conditions, save normally
                    return _superSaveRecord.call(self);
                }
            }).catch(function (error) {
                if (error && error.message === 'SaveCancelled') {
                    return Promise.reject();
                }
                console.error('Error saving record:', error);
                return _superSaveRecord.call(self);
            });
        },

        _showCustomConfirmDialogs: function (conditions) {
            return new Promise((resolve, reject) => {
                const showNextDialog = (index) => {
                    if (index >= conditions.length) {
                        resolve();
                        return;
                    }

                    const condition = conditions[index];
                    new Dialog(this, {
                        title: _t('Confirmation'),
                        size: 'medium',
                        $content: $('<div>').text(condition.message),
                        buttons: [{
                            text: _t('Confirmar'),
                            classes: 'btn-primary',
                            close: true,
                            click: function () {
                                showNextDialog(index + 1);
                            }
                        }, {
                            text: _t('Cancelar'),
                            classes: 'btn-danger',
                            close: true,
                            click: function () {
                                reject();
                            }
                        }]
                    }).open();
                };

                showNextDialog(0);
            });
        }
    });
});
