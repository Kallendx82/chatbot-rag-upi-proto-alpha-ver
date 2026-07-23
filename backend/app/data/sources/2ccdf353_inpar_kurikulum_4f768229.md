# View [inpar.kurikulum] not found. (500 Internal Server Error)

> Source: https://kd-sumedang.upi.edu/inpar/kurikulum

Symfony Exception
Source: inpar_kurikulum_4f768229.html
Symfony Exception
Symfony Docs
InvalidArgumentException
HTTP 500 Internal Server Error
View [inpar.kurikulum] not found.
ExceptionStack Trace
Exception
InvalidArgumentException
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/FileViewFinder.php (line 137)
                    return $viewPath;
                }
            }
        }
        throw new InvalidArgumentException("View [{$name}] not found.");
    }
    /**
     * Get an array of possible view files.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/FileViewFinder.php->findInPaths (line 79)
        if ($this->hasHintInformation($name = trim($name))) {
            return $this->views[$name] = $this->findNamespacedView($name);
        }
        return $this->views[$name] = $this->findInPaths($name, $this->paths);
    }
    /**
     * Get the path to a template with a named path.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Factory.php->find (line 137)
     * @param  array  $mergeData
     * @return \Illuminate\Contracts\View\View
     */
    public function make($view, $data = [], $mergeData = [])
    {
        $path = $this->finder->find(
            $view = $this->normalizeName($view)
        );
        // Next, we will create the view instance and call the view creator for the view
        // which can set any data, etc. Then we will return the view instance back to
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/helpers.php->make (line 1020)
        if (func_num_args() === 0) {
            return $factory;
        }
        return $factory->make($view, $data, $mergeData);
    }
}
view() in /usr/local/www/kdsumedang/routes/web.php (line 971)
Route::get('inpar/sejarah', function () {
    return view('inpar/sejarah');
});
Route::get('inpar/kurikulum', function () {
    return view('inpar/kurikulum');
});
Route::get('inpar/grooming', function () {
    return view('inpar/grooming');
});
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/CallableDispatcher.php->{closure:/usr/local/www/kdsumedang/routes/web.php:970} (line 40)
     * @param  callable  $callable
     * @return mixed
     */
    public function dispatch(Route $route, $callable)
    {
        return $callable(...array_values($this->resolveParameters($route, $callable)));
    }
    /**
     * Resolve the parameters for the callable.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Route.php->dispatch (line 237)
        if ($this->isSerializedClosure()) {
            $callable = unserialize($this->action['uses'])->getClosure();
        }
        return $this->container[CallableDispatcher::class]->dispatch($this, $callable);
    }
    /**
     * Determine if the route action is a serialized Closure.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Route.php->runCallable (line 208)
        try {
            if ($this->isControllerAction()) {
                return $this->runController();
            }
            return $this->runCallable();
        } catch (HttpResponseException $e) {
            return $e->getResponse();
        }
    }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->run (line 806)
        return (new Pipeline($this->container))
                        ->send($request)
                        ->through($middleware)
                        ->then(fn ($request) => $this->prepareResponse(
                            $request, $route->run()
                        ));
    }
    /**
     * Gather the middleware for the given route with resolved class names.
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:Illuminate\Routing\Router::runRouteWithinStack():805} (line 144)
     */
    protected function prepareDestination(Closure $destination)
    {
        return function ($passable) use ($destination) {
            try {
                return $destination($passable);
            } catch (Throwable $e) {
                return $this->handleException($passable, $e);
            }
        };
    }
Pipeline->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142}() in /usr/local/www/kdsumedang/app/Http/Middleware/MinifyHtml.php (line 18)
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
     public function handle($request, Closure $next)
    {
        $response = $next($request);
        if (
            $response instanceof \Illuminate\Http\Response &&
            strpos($response->headers->get('Content-Type'), 'text/html') !== false
        ) {
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Middleware/SubstituteBindings.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 50)
            }
            throw $exception;
        }
        return $next($request);
    }
}
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/VerifyCsrfToken.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 78)
            $this->isReading($request) ||
            $this->runningUnitTests() ||
            $this->inExceptArray($request) ||
            $this->tokensMatch($request)
        ) {
            return tap($next($request), function ($response) use ($request) {
                if ($this->shouldAddXsrfTokenCookie()) {
                    $this->addCookieToResponse($request, $response);
                }
            });
        }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Middleware/ShareErrorsFromSession.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 49)
        // Putting the errors in the view for every view allows the developer to just
        // assume that some errors are always available, which is convenient since
        // they don't have to continually run checks for the presence of errors.
        return $next($request);
    }
}
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 121)
            $this->startSession($request, $session)
        );
        $this->collectGarbage($session);
        $response = $next($request);
        $this->storeCurrentUrl($request, $session);
        $this->addCookieToResponse($response, $session);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php->handleStatefulRequest (line 64)
        if ($this->manager->shouldBlock() ||
            ($request->route() instanceof Route && $request->route()->locksFor())) {
            return $this->handleRequestWhileBlocking($request, $session, $next);
        }
        return $this->handleStatefulRequest($request, $session, $next);
    }
    /**
     * Handle the given request within session state.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/AddQueuedCookiesToResponse.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 37)
     * @param  \Closure  $next
     * @return mixed
     */
    public function handle($request, Closure $next)
    {
        $response = $next($request);
        foreach ($this->cookies->getQueuedCookies() as $cookie) {
            $response->headers->setCookie($cookie);
        }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/EncryptCookies.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 67)
     * @param  \Closure  $next
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function handle($request, Closure $next)
    {
        return $this->encrypt($next($this->decrypt($request)));
    }
    /**
     * Decrypt the cookies on the request.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 119)
    {
        $pipeline = array_reduce(
            array_reverse($this->pipes()), $this->carry(), $this->prepareDestination($destination)
        );
        return $pipeline($this->passable);
    }
    /**
     * Run the pipeline and return the result.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->then (line 805)
        $middleware = $shouldSkipMiddleware ? [] : $this->gatherRouteMiddleware($route);
        return (new Pipeline($this->container))
                        ->send($request)
                        ->through($middleware)
                        ->then(fn ($request) => $this->prepareResponse(
                            $request, $route->run()
                        ));
    }
    /**
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->runRouteWithinStack (line 784)
        $request->setRouteResolver(fn () => $route);
        $this->events->dispatch(new RouteMatched($route, $request));
        return $this->prepareResponse($request,
            $this->runRouteWithinStack($route, $request)
        );
    }
    /**
     * Run the given route within a Stack "onion" instance.
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->runRoute (line 748)
     * @param  \Illuminate\Http\Request  $request
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function dispatchToRoute(Request $request)
    {
        return $this->runRoute($request, $this->findRoute($request));
    }
    /**
     * Find the route matching a given request.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php->dispatchToRoute (line 737)
     */
    public function dispatch(Request $request)
    {
        $this->currentRequest = $request;
        return $this->dispatchToRoute($request);
    }
    /**
     * Dispatch the request to a route and return the response.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php->dispatch (line 200)
    protected function dispatchToRouter()
    {
        return function ($request) {
            $this->app->instance('request', $request);
            return $this->router->dispatch($request);
        };
    }
    /**
     * Call the terminate method on any terminable middleware.
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:Illuminate\Foundation\Http\Kernel::dispatchToRouter():197} (line 144)
     */
    protected function prepareDestination(Closure $destination)
    {
        return function ($passable) use ($destination) {
            try {
                return $destination($passable);
            } catch (Throwable $e) {
                return $this->handleException($passable, $e);
            }
        };
    }
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142} (line 21)
     */
    public function handle($request, Closure $next)
    {
        $this->clean($request);
        return $next($request);
    }
    /**
     * Clean the request's data.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ConvertEmptyStringsToNull.php->handle (line 31)
            if ($callback($request)) {
                return $next($request);
            }
        }
        return parent::handle($request, $next);
    }
    /**
     * Transform the given value.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 21)
     */
    public function handle($request, Closure $next)
    {
        $this->clean($request);
        return $next($request);
    }
    /**
     * Clean the request's data.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TrimStrings.php->handle (line 40)
            if ($callback($request)) {
                return $next($request);
            }
        }
        return parent::handle($request, $next);
    }
    /**
     * Transform the given value.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ValidatePostSize.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 27)
        if ($max > 0 && $request->server('CONTENT_LENGTH') > $max) {
            throw new PostTooLargeException;
        }
        return $next($request);
    }
    /**
     * Determine the server 'post_max_size' as bytes.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/PreventRequestsDuringMaintenance.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 99)
                null,
                $this->getHeaders($data)
            );
        }
        return $next($request);
    }
    /**
     * Determine if the incoming request has a maintenance mode bypass cookie.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/HandleCors.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 49)
     * @return \Illuminate\Http\Response
     */
    public function handle($request, Closure $next)
    {
        if (! $this->hasMatchingPath($request)) {
            return $next($request);
        }
        $this->cors->setOptions($this->container['config']->get('cors', []));
        if ($this->cors->isPreflightRequest($request)) {
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/TrustProxies.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 39)
    {
        $request::setTrustedProxies([], $this->getTrustedHeaderNames());
        $this->setTrustedProxyIpAddresses($request);
        return $next($request);
    }
    /**
     * Sets the trusted proxies on the request.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->handle (line 183)
                        // since the object we're given was already a fully instantiated object.
                        $parameters = [$passable, $stack];
                    }
                    $carry = method_exists($pipe, $this->method)
                                    ? $pipe->{$this->method}(...$parameters)
                                    : $pipe(...$parameters);
                    return $this->handleCarry($carry);
                } catch (Throwable $e) {
                    return $this->handleException($passable, $e);
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159} (line 119)
    {
        $pipeline = array_reduce(
            array_reverse($this->pipes()), $this->carry(), $this->prepareDestination($destination)
        );
        return $pipeline($this->passable);
    }
    /**
     * Run the pipeline and return the result.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php->then (line 175)
        $this->bootstrap();
        return (new Pipeline($this->app))
                    ->send($request)
                    ->through($this->app->shouldSkipMiddleware() ? [] : $this->middleware)
                    ->then($this->dispatchToRouter());
    }
    /**
     * Bootstrap the application for HTTP requests.
     *
in /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php->sendRequestThroughRouter (line 144)
        $this->requestStartedAt = Carbon::now();
        try {
            $request->enableHttpMethodParameterOverride();
            $response = $this->sendRequestThroughRouter($request);
        } catch (Throwable $e) {
            $this->reportException($e);
            $response = $this->renderException($request, $e);
        }
Kernel->handle() in /usr/local/www/kdsumedang/public/index.php (line 51)
$app = require_once __DIR__.'/../bootstrap/app.php';
$kernel = $app->make(Kernel::class);
$response = $kernel->handle(
    $request = Request::capture()
)->send();
$kernel->terminate($request, $response);
Stack Trace
InvalidArgumentException

 InvalidArgumentException: View [inpar.kurikulum] not found. at /usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/FileViewFinder.php:137 at Illuminate\View\FileViewFinder->findInPaths() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/FileViewFinder.php:79) at Illuminate\View\FileViewFinder->find() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Factory.php:137) at Illuminate\View\Factory->make() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/helpers.php:1020) at view() (/usr/local/www/kdsumedang/routes/web.php:971) at Illuminate\Routing\RouteFileRegistrar->{closure:/usr/local/www/kdsumedang/routes/web.php:970}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/CallableDispatcher.php:40) at Illuminate\Routing\CallableDispatcher->dispatch() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Route.php:237) at Illuminate\Routing\Route->runCallable() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Route.php:208) at Illuminate\Routing\Route->run() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:806) at Illuminate\Routing\Router->{closure:Illuminate\Routing\Router::runRouteWithinStack():805}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:144) at Illuminate\Pipeline\Pipeline->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142}() (/usr/local/www/kdsumedang/app/Http/Middleware/MinifyHtml.php:18) at App\Http\Middleware\MinifyHtml->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Middleware/SubstituteBindings.php:50) at Illuminate\Routing\Middleware\SubstituteBindings->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/VerifyCsrfToken.php:78) at Illuminate\Foundation\Http\Middleware\VerifyCsrfToken->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/View/Middleware/ShareErrorsFromSession.php:49) at Illuminate\View\Middleware\ShareErrorsFromSession->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php:121) at Illuminate\Session\Middleware\StartSession->handleStatefulRequest() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Session/Middleware/StartSession.php:64) at Illuminate\Session\Middleware\StartSession->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/AddQueuedCookiesToResponse.php:37) at Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Cookie/Middleware/EncryptCookies.php:67) at Illuminate\Cookie\Middleware\EncryptCookies->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:119) at Illuminate\Pipeline\Pipeline->then() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:805) at Illuminate\Routing\Router->runRouteWithinStack() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:784) at Illuminate\Routing\Router->runRoute() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:748) at Illuminate\Routing\Router->dispatchToRoute() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Routing/Router.php:737) at Illuminate\Routing\Router->dispatch() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php:200) at Illuminate\Foundation\Http\Kernel->{closure:Illuminate\Foundation\Http\Kernel::dispatchToRouter():197}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:144) at Illuminate\Pipeline\Pipeline->{closure:Illuminate\Pipeline\Pipeline::prepareDestination():142}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php:21) at Illuminate\Foundation\Http\Middleware\TransformsRequest->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ConvertEmptyStringsToNull.php:31) at Illuminate\Foundation\Http\Middleware\ConvertEmptyStringsToNull->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TransformsRequest.php:21) at Illuminate\Foundation\Http\Middleware\TransformsRequest->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/TrimStrings.php:40) at Illuminate\Foundation\Http\Middleware\TrimStrings->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/ValidatePostSize.php:27) at Illuminate\Foundation\Http\Middleware\ValidatePostSize->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Middleware/PreventRequestsDuringMaintenance.php:99) at Illuminate\Foundation\Http\Middleware\PreventRequestsDuringMaintenance->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/HandleCors.php:49) at Illuminate\Http\Middleware\HandleCors->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Http/Middleware/TrustProxies.php:39) at Illuminate\Http\Middleware\TrustProxies->handle() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:183) at Illuminate\Pipeline\Pipeline->{closure:{closure:Illuminate\Pipeline\Pipeline::carry():158}:159}() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Pipeline/Pipeline.php:119) at Illuminate\Pipeline\Pipeline->then() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php:175) at Illuminate\Foundation\Http\Kernel->sendRequestThroughRouter() (/usr/local/www/kdsumedang/vendor/laravel/framework/src/Illuminate/Foundation/Http/Kernel.php:144) at Illuminate\Foundation\Http\Kernel->handle() (/usr/local/www/kdsumedang/public/index.php:51)
