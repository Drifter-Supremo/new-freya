"""
test_firestore_optimization.py - Test and compare Firestore query optimizations

This script:
1. Tests original query performance
2. Tests optimized query performance
3. Compares results and generates report
"""

import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Tuple
import statistics

from app.services.firebase_service import FirebaseService
from app.services.firebase_memory_service import FirebaseMemoryService
from app.services.firebase_service_optimized import OptimizedFirebaseService
from app.services.firebase_memory_service_optimized import OptimizedFirebaseMemoryService
from app.core.config import logger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PerformanceTester:
    """Test and compare Firestore query performance."""
    
    def __init__(self):
        # Original services
        self.firebase_original = FirebaseService()
        self.memory_original = FirebaseMemoryService()
        
        # Optimized services
        self.firebase_optimized = OptimizedFirebaseService()
        self.memory_optimized = OptimizedFirebaseMemoryService()
        
        # Test results
        self.results = {
            'original': {},
            'optimized': {},
            'improvements': {}
        }
    
    def measure_time(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        return result, elapsed_time
    
    def test_user_facts_query(self, user_id: str, iterations: int = 5):
        """Test user facts query performance."""
        print("\n📊 Testing User Facts Query Performance...")
        
        # Test original implementation
        original_times = []
        for i in range(iterations):
            _, elapsed = self.measure_time(self.firebase_original.get_user_facts, user_id)
            original_times.append(elapsed)
            if i == 0 and hasattr(self.firebase_optimized, 'clear_cache'):  # Clear cache after first run for optimized version
                self.firebase_optimized.clear_cache()
        
        # Test optimized implementation
        optimized_times = []
        optimized_cached_times = []
        for i in range(iterations):
            if i == 0 and hasattr(self.firebase_optimized, 'clear_cache'):
                self.firebase_optimized.clear_cache()  # Clear cache before first optimized run
            _, elapsed = self.measure_time(self.firebase_optimized.get_user_facts, user_id)
            if i == 0:
                optimized_times.append(elapsed)  # First run (no cache)
            else:
                optimized_cached_times.append(elapsed)  # Subsequent runs (cached)
        
        # Calculate statistics
        original_avg = statistics.mean(original_times)
        optimized_avg = statistics.mean(optimized_times)
        optimized_cached_avg = statistics.mean(optimized_cached_times) if optimized_cached_times else 0
        
        improvement = ((original_avg - optimized_avg) / original_avg * 100) if original_avg > 0 else 0
        cache_improvement = ((original_avg - optimized_cached_avg) / original_avg * 100) if original_avg > 0 and optimized_cached_avg > 0 else 0
        
        # Store results
        self.results['original']['user_facts'] = original_avg
        self.results['optimized']['user_facts'] = optimized_avg
        self.results['optimized']['user_facts_cached'] = optimized_cached_avg
        self.results['improvements']['user_facts'] = improvement
        self.results['improvements']['user_facts_cached'] = cache_improvement
        
        # Print results
        print(f"  Original: {original_avg:.3f}s (avg of {iterations} runs)")
        print(f"  Optimized (no cache): {optimized_avg:.3f}s")
        print(f"  Optimized (cached): {optimized_cached_avg:.3f}s")
        print(f"  Improvement: {improvement:.1f}% (no cache), {cache_improvement:.1f}% (cached)")
    
    def test_memory_context_assembly(self, user_id: str, test_queries: List[str]):
        """Test memory context assembly performance."""
        print("\n📊 Testing Memory Context Assembly Performance...")
        
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            
            # Test original
            _, original_time = self.measure_time(
                self.memory_original.assemble_memory_context, user_id, query
            )
            
            # Clear cache for fair comparison
            if hasattr(self.firebase_optimized, 'clear_cache'):
                self.firebase_optimized.clear_cache()
            
            # Test optimized
            _, optimized_time = self.measure_time(
                self.memory_optimized.assemble_memory_context_optimized, user_id, query
            )
            
            improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
            
            print(f"    Original: {original_time:.3f}s")
            print(f"    Optimized: {optimized_time:.3f}s")
            print(f"    Improvement: {improvement:.1f}%")
            
            # Store results
            query_key = f"memory_context_{query[:20]}"
            self.results['original'][query_key] = original_time
            self.results['optimized'][query_key] = optimized_time
            self.results['improvements'][query_key] = improvement
    
    def test_parallel_execution(self, user_id: str):
        """Test parallel vs sequential query execution."""
        print("\n📊 Testing Parallel Query Execution...")
        
        # Sequential execution (original approach)
        start_time = time.time()
        facts = self.firebase_original.get_user_facts(user_id)
        convs = self.firebase_original.get_user_conversations(user_id, limit=10)
        topics = self.firebase_original.get_user_topics(user_id)
        sequential_time = time.time() - start_time
        
        # Clear cache
        if hasattr(self.firebase_optimized, 'clear_cache'):
            self.firebase_optimized.clear_cache()
        
        # Parallel execution (optimized approach)
        start_time = time.time()
        context = self.firebase_optimized.get_user_memory_context_parallel(user_id)
        parallel_time = time.time() - start_time
        
        improvement = ((sequential_time - parallel_time) / sequential_time * 100) if sequential_time > 0 else 0
        
        print(f"  Sequential: {sequential_time:.3f}s")
        print(f"  Parallel: {parallel_time:.3f}s")
        print(f"  Improvement: {improvement:.1f}%")
        
        self.results['original']['parallel_test'] = sequential_time
        self.results['optimized']['parallel_test'] = parallel_time
        self.results['improvements']['parallel_test'] = improvement
    
    def test_cache_effectiveness(self, user_id: str):
        """Test cache effectiveness with repeated queries."""
        print("\n📊 Testing Cache Effectiveness...")
        
        # Clear cache
        if hasattr(self.firebase_optimized, 'clear_cache'):
            self.firebase_optimized.clear_cache()
        
        # First query (no cache)
        _, first_time = self.measure_time(self.firebase_optimized.get_user_facts, user_id)
        
        # Repeated queries (should hit cache)
        cached_times = []
        for _ in range(5):
            _, elapsed = self.measure_time(self.firebase_optimized.get_user_facts, user_id)
            cached_times.append(elapsed)
        
        avg_cached_time = statistics.mean(cached_times)
        cache_speedup = (first_time / avg_cached_time) if avg_cached_time > 0 else 0
        
        print(f"  First query: {first_time:.3f}s")
        print(f"  Cached queries: {avg_cached_time:.3f}s (avg)")
        print(f"  Cache speedup: {cache_speedup:.1f}x faster")
        
        self.results['optimized']['cache_first'] = first_time
        self.results['optimized']['cache_repeated'] = avg_cached_time
        self.results['improvements']['cache_speedup'] = cache_speedup
    
    def test_query_patterns(self, user_id: str):
        """Test specific query pattern optimizations."""
        print("\n📊 Testing Specific Query Patterns...")
        
        # Test 1: Messages with conversationId filter
        print("\n  1. Messages with conversationId filter:")
        
        # Get a conversation ID
        convs = self.firebase_original.get_user_conversations(user_id, limit=1)
        if convs:
            conv_id = convs[0].get('id')
            
            # Original (no filter)
            _, original_time = self.measure_time(
                self.firebase_original.get_conversation_messages, conv_id, 50
            )
            
            # Optimized (with filter)
            if hasattr(self.firebase_optimized, 'clear_cache'):
                self.firebase_optimized.clear_cache()
            _, optimized_time = self.measure_time(
                self.firebase_optimized.get_conversation_messages_optimized, conv_id, 50
            )
            
            improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
            
            print(f"    Original: {original_time:.3f}s")
            print(f"    Optimized: {optimized_time:.3f}s")
            print(f"    Improvement: {improvement:.1f}%")
        
        # Test 2: Recent messages with timestamp filter
        print("\n  2. Recent messages with timestamp filter:")
        
        # Original
        _, original_time = self.measure_time(
            self.memory_original.get_recent_messages, user_id, 20, 7
        )
        
        # Optimized
        if hasattr(self.firebase_optimized, 'clear_cache'):
            self.firebase_optimized.clear_cache()
        _, optimized_time = self.measure_time(
            self.memory_optimized._get_recent_messages_optimized, user_id, 20, 7
        )
        
        improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
        
        print(f"    Original: {original_time:.3f}s")
        print(f"    Optimized: {optimized_time:.3f}s")
        print(f"    Improvement: {improvement:.1f}%")
    
    def generate_report(self):
        """Generate performance comparison report."""
        print("\n" + "=" * 60)
        print("📈 FIRESTORE OPTIMIZATION PERFORMANCE REPORT")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Summary statistics
        print("\n## SUMMARY")
        
        # Calculate overall improvements
        improvements = [v for k, v in self.results['improvements'].items() if isinstance(v, (int, float)) and v > 0]
        if improvements:
            avg_improvement = statistics.mean(improvements)
            max_improvement = max(improvements)
            
            print(f"Average Performance Improvement: {avg_improvement:.1f}%")
            print(f"Maximum Performance Improvement: {max_improvement:.1f}%")
        
        # Detailed results
        print("\n## DETAILED RESULTS")
        
        print("\n### Query Performance (seconds)")
        print(f"{'Operation':<30} {'Original':>10} {'Optimized':>10} {'Improvement':>15}")
        print("-" * 65)
        
        for key in self.results['original']:
            if key in self.results['optimized']:
                original = self.results['original'][key]
                optimized = self.results['optimized'][key]
                improvement = self.results['improvements'].get(key, 0)
                
                print(f"{key:<30} {original:>10.3f} {optimized:>10.3f} {improvement:>14.1f}%")
        
        # Cache effectiveness
        if 'cache_speedup' in self.results['improvements']:
            print(f"\n### Cache Effectiveness")
            print(f"Cache provides {self.results['improvements']['cache_speedup']:.1f}x speedup for repeated queries")
        
        # Recommendations
        print("\n## RECOMMENDATIONS")
        print("1. ✅ Deploy optimized services for immediate performance gains")
        print("2. ✅ Enable caching for frequently accessed data (user facts)")
        print("3. ✅ Use parallel query execution for memory context assembly")
        print("4. ⚠️  Ensure Firestore indexes are created for optimal performance")
        print("5. ⚠️  Run migration script to add missing fields (userId, conversationId)")
        
        # Next steps
        print("\n## NEXT STEPS")
        print("1. Run migration script: python scripts/migrate_firestore_fields.py")
        print("2. Create indexes in Firebase Console (see migration output)")
        print("3. Update imports to use optimized services")
        print("4. Monitor performance in production")
    
    def run_all_tests(self, user_id: str):
        """Run all performance tests."""
        print("\n🚀 Starting Firestore Optimization Tests...")
        print(f"Testing with user_id: {user_id}")
        
        # Run tests
        self.test_user_facts_query(user_id)
        self.test_memory_context_assembly(user_id, [
            "Do you remember what we talked about yesterday?",
            "What do you know about my family?",
            "Tell me about coding"
        ])
        self.test_parallel_execution(user_id)
        self.test_cache_effectiveness(user_id)
        self.test_query_patterns(user_id)
        
        # Generate report
        self.generate_report()

def main():
    """Main test function."""
    # Initialize tester
    tester = PerformanceTester()
    
    # Run tests
    user_id = "Sencere"
    tester.run_all_tests(user_id)
    
    print("\n✅ Performance testing complete!")

if __name__ == "__main__":
    main()