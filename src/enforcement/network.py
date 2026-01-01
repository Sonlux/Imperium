#!/usr/bin/env python3
"""
Network Enforcement Module - Applies traffic control policies
Uses tc (traffic control) for bandwidth and latency management
"""
import subprocess
import logging
from typing import Dict, Any
import platform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetworkEnforcer:
    """Enforces network policies using Linux traffic control"""
    
    def __init__(self, interface='eth0'):
        self.interface = interface
        self.is_linux = platform.system() == 'Linux'
        
        if not self.is_linux:
            logger.warning("Not running on Linux - enforcement will be simulated")
    
    def apply_policy(self, policy: Dict[str, Any]) -> bool:
        """
        Apply a network policy
        
        Args:
            policy: Policy dictionary with type, target, and parameters
            
        Returns:
            bool: Success status
        """
        policy_type = policy.get('policy_type')
        
        if policy_type == 'traffic_shaping':
            return self._apply_traffic_shaping(policy)
        elif policy_type == 'bandwidth_limit':
            return self._apply_bandwidth_limit(policy)
        elif policy_type == 'routing_priority':
            return self._apply_routing_priority(policy)
        else:
            logger.warning(f"Unknown policy type: {policy_type}")
            return False
    
    def _apply_traffic_shaping(self, policy: Dict) -> bool:
        """Apply traffic shaping policy using HTB (Hierarchical Token Bucket)"""
        params = policy.get('parameters', {})
        target = policy.get('target')
        
        logger.info(f"Applying traffic shaping for {target}: {params}")
        
        if not self.is_linux:
            logger.info("Simulated: Would execute tc commands")
            return True
        
        try:
            # Create root qdisc
            self._run_tc_command([
                'qdisc', 'add', 'dev', self.interface,
                'root', 'handle', '1:', 'htb', 'default', '30'
            ])
            
            # Create class for high priority traffic
            rate = params.get('rate', '100mbit')
            ceil = params.get('ceil', '200mbit')
            burst = params.get('burst', '32k')
            
            self._run_tc_command([
                'class', 'add', 'dev', self.interface,
                'parent', '1:', 'classid', '1:1', 'htb',
                'rate', rate, 'ceil', ceil, 'burst', burst
            ])
            
            logger.info("Traffic shaping applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply traffic shaping: {e}")
            return False
    
    def _apply_bandwidth_limit(self, policy: Dict) -> bool:
        """Apply bandwidth limitation"""
        params = policy.get('parameters', {})
        target = policy.get('target')
        
        logger.info(f"Applying bandwidth limit for {target}: {params}")
        
        if not self.is_linux:
            logger.info("Simulated: Would limit bandwidth")
            return True
        
        try:
            rate = params.get('rate', '100mbit')
            
            # Use TBF (Token Bucket Filter) for simple rate limiting
            self._run_tc_command([
                'qdisc', 'add', 'dev', self.interface,
                'root', 'tbf', 'rate', rate,
                'burst', '32kbit', 'latency', '400ms'
            ])
            
            logger.info("Bandwidth limit applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply bandwidth limit: {e}")
            return False
    
    def _apply_routing_priority(self, policy: Dict) -> bool:
        """Apply routing priority using iptables marking"""
        params = policy.get('parameters', {})
        target = policy.get('target')
        
        logger.info(f"Applying routing priority for {target}: {params}")
        
        if not self.is_linux:
            logger.info("Simulated: Would set routing priority")
            return True
        
        try:
            tos = params.get('tos', '0x10')
            
            # Mark packets with TOS (Type of Service)
            subprocess.run([
                'iptables', '-t', 'mangle', '-A', 'POSTROUTING',
                '-j', 'TOS', '--set-tos', tos
            ], check=True)
            
            logger.info("Routing priority applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply routing priority: {e}")
            return False
    
    def _run_tc_command(self, args):
        """Execute tc command"""
        cmd = ['tc'] + args
        logger.debug(f"Executing: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"tc command failed: {result.stderr}")
            raise Exception(f"tc failed: {result.stderr}")
        
        return result.stdout
    
    def clear_policies(self) -> bool:
        """Clear all traffic control rules"""
        logger.info(f"Clearing all policies on {self.interface}")
        
        if not self.is_linux:
            logger.info("Simulated: Would clear policies")
            return True
        
        try:
            self._run_tc_command(['qdisc', 'del', 'dev', self.interface, 'root'])
            logger.info("Policies cleared successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to clear policies: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current traffic control status"""
        if not self.is_linux:
            return {'status': 'simulated', 'interface': self.interface}
        
        try:
            output = self._run_tc_command(['qdisc', 'show', 'dev', self.interface])
            return {
                'status': 'active',
                'interface': self.interface,
                'rules': output
            }
        except Exception as e:
            return {
                'status': 'error',
                'interface': self.interface,
                'error': str(e)
            }


if __name__ == '__main__':
    # Test the enforcer
    enforcer = NetworkEnforcer('eth0')
    
    test_policy = {
        'policy_id': 'test-1',
        'policy_type': 'bandwidth_limit',
        'target': 'node-1',
        'parameters': {
            'rate': '100mbit',
            'ceil': '200mbit'
        }
    }
    
    logger.info("Testing network enforcer...")
    result = enforcer.apply_policy(test_policy)
    logger.info(f"Policy application result: {result}")
    
    status = enforcer.get_status()
    logger.info(f"Current status: {status}")
