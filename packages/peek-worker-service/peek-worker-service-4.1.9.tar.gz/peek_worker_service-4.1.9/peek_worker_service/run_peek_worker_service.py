#!/usr/bin/env python
"""

  Copyright Synerty Pty Ltd 2013

  This software is proprietary, you are not free to copy
  or redistribute this code in any format.

  All rights to this software are reserved by
  Synerty Pty Ltd

"""

import logging
import threading
from threading import Thread

from setproctitle import setproctitle
from reactivex import operators

from peek_platform import PeekPlatformConfig
from peek_platform.util.LogUtil import (
    setupPeekLogger,
    updatePeekLoggerHandlers,
    setupLoggingToSyslogServer,
)
from peek_platform.util.ManHoleUtil import start_manhole
from peek_plugin_base.PeekVortexUtil import peekWorkerName, peekServerName
from pytmpdir.dir_setting import DirSetting
from twisted.internet import reactor, defer
from txhttputil.site.FileUploadRequest import FileUploadRequest
from vortex.DeferUtil import vortexLogFailure
from vortex.VortexFactory import VortexFactory

setupPeekLogger(peekWorkerName)

logger = logging.getLogger(__name__)


def setupPlatform():
    from peek_platform import PeekPlatformConfig

    PeekPlatformConfig.componentName = peekWorkerName
    setproctitle(PeekPlatformConfig.componentName)

    # Tell the platform classes about our instance of the pluginSwInstallManager
    from peek_worker_service.sw_install.PluginSwInstallManager import (
        PluginSwInstallManager,
    )

    PeekPlatformConfig.pluginSwInstallManager = PluginSwInstallManager()

    # Tell the platform classes about our instance of the PeekSwInstallManager
    from peek_worker_service.sw_install.PeekSwInstallManager import (
        PeekSwInstallManager,
    )

    PeekPlatformConfig.peekSwInstallManager = PeekSwInstallManager()

    # Tell the platform classes about our instance of the PeekLoaderBase
    from peek_worker_service.plugin.WorkerPluginLoader import WorkerPluginLoader

    PeekPlatformConfig.pluginLoader = WorkerPluginLoader()

    # The config depends on the componentName, order is important
    from peek_worker_service.PeekWorkerConfig import PeekWorkerConfig

    PeekPlatformConfig.config = PeekWorkerConfig()

    # Update the version in the config file
    from peek_worker_service import __version__

    PeekPlatformConfig.config.platformVersion = __version__

    # Set default logging level
    logging.root.setLevel(PeekPlatformConfig.config.loggingLevel)

    # PsUtil
    if not PeekPlatformConfig.config.loggingLogSystemMetrics:
        logging.getLogger("peek_plugin_base.util.PeekPsUtil").setLevel(999)

    updatePeekLoggerHandlers(
        PeekPlatformConfig.componentName,
        PeekPlatformConfig.config.daysToKeep,
        PeekPlatformConfig.config.logToStdout,
    )

    if PeekPlatformConfig.config.loggingLogToSyslogHost:
        setupLoggingToSyslogServer(
            PeekPlatformConfig.config.loggingLogToSyslogHost,
            PeekPlatformConfig.config.loggingLogToSyslogPort,
            PeekPlatformConfig.config.loggingLogToSyslogFacility,
        )

    # Enable deferred debugging if DEBUG is on.
    if logging.root.level == logging.DEBUG:
        defer.setDebugging(True)

    # If we need to enable memory debugging, turn that on.
    if PeekPlatformConfig.config.loggingDebugMemoryMask:
        from peek_platform.util.MemUtil import setupMemoryDebugging

        setupMemoryDebugging(
            PeekPlatformConfig.componentName,
            PeekPlatformConfig.config.loggingDebugMemoryMask,
        )

    # The worker doesn't need any threads
    reactor.suggestThreadPoolSize(1)

    # Initialise the txhttputil Directory object
    DirSetting.defaultDirChmod = PeekPlatformConfig.config.DEFAULT_DIR_CHMOD
    DirSetting.tmpDirPath = PeekPlatformConfig.config.tmpPath
    FileUploadRequest.tmpFilePath = PeekPlatformConfig.config.tmpPath

    # Configure the celery app in the worker
    # This is not the worker that will be started, it allows the worker to queue tasks
    from peek_platform.ConfigCeleryApp import configureCeleryApp
    from peek_platform import PeekPlatformConfig
    from peek_plugin_base.worker.CeleryApp import celeryApp

    configureCeleryApp(celeryApp, PeekPlatformConfig.config)

    # Setup manhole
    if PeekPlatformConfig.config.manholeEnabled:
        start_manhole(
            PeekPlatformConfig.config.manholePort,
            PeekPlatformConfig.config.manholePassword,
            PeekPlatformConfig.config.manholePublicKeyFile,
            PeekPlatformConfig.config.manholePrivateKeyFile,
        )


def twistedMain():
    # defer.setDebugging(True)
    # sys.argv.remove(DEBUG_ARG)
    # import pydevd
    # pydevd.settrace(suspend=False)

    # Make the agent restart when the server restarts, or when it looses connection
    def restart(_=None):
        from peek_platform import PeekPlatformConfig

        PeekPlatformConfig.peekSwInstallManager.restartProcess()

    (
        VortexFactory.subscribeToVortexStatusChange(peekServerName)
        .pipe(operators.filter(lambda online: online == False))
        .subscribe(on_next=restart)
    )

    # First, setup the VortexServer Worker
    from peek_platform import PeekPlatformConfig

    dataExchangeCfg = PeekPlatformConfig.config.dataExchange

    scheme = "wss" if dataExchangeCfg.peekServerUseSSL else "ws"
    host = dataExchangeCfg.peekServerHost
    port = dataExchangeCfg.peekServerHttpPort

    def start():
        d = VortexFactory.createWebsocketClient(
            PeekPlatformConfig.componentName,
            host,
            port,
            url=f"{scheme}://{host}:{port}/vortexws",
            sslEnableMutualTLS=dataExchangeCfg.peekServerSSLEnableMutualTLS,
            sslClientCertificateBundleFilePath=dataExchangeCfg.peekServerSSLClientBundleFilePath,
            sslMutualTLSCertificateAuthorityBundleFilePath=dataExchangeCfg.peekServerSSLClientMutualTLSCertificateAuthorityBundleFilePath,
            sslMutualTLSTrustedPeerCertificateBundleFilePath=dataExchangeCfg.peekServerSSLMutualTLSTrustedPeerCertificateBundleFilePath,
        )

        d.addErrback(vortexLogFailure, logger, consumeError=True)

        # Software update check is not a thing any more
        # Start Update Handler,
        # Add both, The peek client_fe_app might fail to connect, and if it does, the payload
        # sent from the peekSwUpdater will be queued and sent when it does connect.
        # d.addBoth(lambda _: peekSwVersionPollHandler.start())

        # Load all Plugins

        d.addBoth(lambda _: logger.info("Loading all Peek Plugins"))
        d.addBoth(lambda _: PeekPlatformConfig.pluginLoader.loadCorePlugins())
        d.addBoth(
            lambda _: PeekPlatformConfig.pluginLoader.loadOptionalPlugins()
        )

        d.addBoth(lambda _: logger.info("Starting all Peek Plugins"))
        d.addBoth(lambda _: PeekPlatformConfig.pluginLoader.startCorePlugins())
        d.addBoth(
            lambda _: PeekPlatformConfig.pluginLoader.startOptionalPlugins()
        )

        # Log Exception, convert the errback to callback
        d.addErrback(vortexLogFailure, logger, consumeError=False)
        d.addErrback(lambda _: restart())

        # Log that the reactor has started
        d.addCallback(
            lambda _: logger.info(
                "Peek Worker is running, version=%s",
                PeekPlatformConfig.config.platformVersion,
            )
        )

        # Unlock the mutex
        d.addCallback(lambda _: twistedPluginsLoadedMutex.release())

        d.addErrback(vortexLogFailure, logger, consumeError=True)

    # Run the reactor in a thread
    reactor.callLater(0, logger.info, "Reactor started")
    reactor.callLater(0, start)

    reactor.run(installSignalHandlers=False)


def celeryMain():
    from peek_platform import PeekPlatformConfig

    # Load all Plugins
    logger.info("Starting Celery")
    from peek_worker_service import CeleryApp

    CeleryApp.start(PeekPlatformConfig.config)


# Create the startup mutex, twisted has to load the plugins before celery starts.
twistedPluginsLoadedMutex = threading.Lock()
assert twistedPluginsLoadedMutex.acquire()


def setPeekWorkerRestarting():
    global peekWorkerRestarting
    peekWorkerRestarting = True


def main():
    setupPlatform()

    # Initialise and run all the twisted stuff in another thread.
    twistedMainLoopThread = Thread(target=twistedMain)
    twistedMainLoopThread.start()

    # Block until twisted has released it's lock
    twistedPluginsLoadedMutex.acquire()

    # Start the celery blocking main thread
    celeryMain()
    logger.info("Celery has shutdown")

    # Shutdown the Vortex
    VortexFactory.shutdown()

    if PeekPlatformConfig.peekSwInstallManager.restartTriggered:
        logger.info("Restarting Peek Worker")
        PeekPlatformConfig.peekSwInstallManager.realyRestartProcess()

    else:
        # Tell twisted to stop
        logger.info("Shutting down twisted reactor.")
        reactor.callFromThread(reactor.stop)

    # Wait for twisted to stop
    twistedMainLoopThread.join()
    logger.info("Reactor shutdown complete.")

    PeekPlatformConfig.pluginLoader.stopCorePlugins()
    PeekPlatformConfig.pluginLoader.stopOptionalPlugins()

    PeekPlatformConfig.pluginLoader.unloadCorePlugins()
    PeekPlatformConfig.pluginLoader.unloadOptionalPlugins()
    logger.info("Worker Service shutdown complete.")


if __name__ == "__main__":
    main()
