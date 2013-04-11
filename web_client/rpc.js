(function () {
  /* global angular */
  var module = angular.module('rpc', []);


  module.service('rpc', [
    '$q', '$rootScope', 'websocket',
    function ($q, rootScope, ws) {
      var last_id = 0;

      function auto_id() {
        last_id += 1;
        return last_id;
      }

      function RpcCall(scope, service, method, args) {
        var self = this;
        this.deferred = $q.defer();
        this.scope = scope;
        this.service = service;
        this.method = method;
        this.args = args;
        this.handles_error = false;
        this.finalizer = null;
        this.handler_promises = [];
        this.finalizer_promise = $q.defer();
      }

      RpcCall.prototype = {
        send:             function () {
          var msg = JSON.stringify({
            id:      auto_id(),
            service: this.service,
            method:  this.method,
            args:    this.args
          });
          ws.send(msg);
        },
        then:             function (callback, errback) {
          var promise = this.deferred.promise.then(callback, errback);
          if (errback) {
            this.handles_error = true;
          }
          self.handler_promises.push(promise);
        },
        finalize:         function (callback, errback) {
          return this.finalizer_promise.then(callback, errback);
        },
        process_response: function (response) {
          var self = this, fire_finalizers;
          if (response.success) {
            self.deferred.resolve(response.result);
          } else {
            self.deferred.reject(response.error);
          }
          fire_finalizers = function (value) {
            self.finalizer_promise.resolve(value);
          };
          $q.all(this.handler_promises).then(fire_finalizers);
        }
      };

      function rpc(svc_dot_method, args) {
        var scope = this,
          split_svc = svc_dot_method.split('.'),
          svc = split_svc[0],
          method = split_svc[1],
          call = RpcCall(scope, service, method, args);
        call.finalize(null, function (error) {
          scope.$emit('rpc.' + error.type, error);
        });
        ws.send(JSON.stringify())
        return call.deferred.promise;
      }
    }
  ]);

}());
