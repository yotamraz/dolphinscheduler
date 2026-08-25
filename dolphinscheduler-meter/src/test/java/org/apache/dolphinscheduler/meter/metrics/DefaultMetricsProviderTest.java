/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.dolphinscheduler.meter.metrics;

import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DefaultMetricsProviderTest {

    private SimpleMeterRegistry registry;
    private DefaultMetricsProvider provider;

    @BeforeEach
    void setUp() {
        registry = new SimpleMeterRegistry();
        provider = new DefaultMetricsProvider(registry);
    }

    @Test
    void gaugeOrFallback_meterNotRegistered_returnsFallback() {
        SystemMetrics metrics = provider.getSystemMetrics();
        assertEquals(0.0, metrics.getSystemCpuUsagePercentage(), 1e-9,
                "Expected fallback 0.0 when system.cpu.usage gauge is absent");
    }

    @Test
    void gaugeOrFallback_meterRegisteredButNaN_returnsFallback() {
        Gauge.builder("system.cpu.usage", () -> Double.NaN).register(registry);
        SystemMetrics metrics = provider.getSystemMetrics();
        assertEquals(0.0, metrics.getSystemCpuUsagePercentage(), 1e-9,
                "Expected fallback 0.0 when system.cpu.usage gauge returns NaN");
    }

    @Test
    void gaugeOrFallback_meterRegisteredWithValidValue_returnsValue() {
        Gauge.builder("system.cpu.usage", () -> 0.42).register(registry);
        SystemMetrics metrics = provider.getSystemMetrics();
        assertEquals(0.42, metrics.getSystemCpuUsagePercentage(), 1e-9,
                "Expected the real gauge value when system.cpu.usage is registered and valid");
    }

    @Test
    void gaugeOrFallback_diskGaugesAbsent_usesStickyFallbacks_zeroUsagePercentage() {
        // With sticky fallbacks initialized to lastDiskTotalBytes=1.0 and lastDiskFreeBytes=1.0,
        // diskUsedPercentage = (1.0 - 1.0) / 1.0 = 0.0 — safe startup state, no divide-by-zero.
        SystemMetrics metrics = provider.getSystemMetrics();
        assertEquals(0.0, metrics.getDiskUsedPercentage(), 1e-9,
                "Expected diskUsedPercentage=0.0 during startup before disk gauges are registered");
    }
}
