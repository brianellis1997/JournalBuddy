'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, BookOpen, Target, MessageCircle, Trophy, LogOut, Mic } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/store/authStore';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/buddy', label: 'Talk to Buddy', icon: Mic, highlight: true },
  { href: '/journal', label: 'Journal', icon: BookOpen },
  { href: '/goals', label: 'Goals', icon: Target },
  { href: '/chat', label: 'AI Chat', icon: MessageCircle },
  { href: '/progress', label: 'Progress', icon: Trophy },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-primary-600">JournalBuddy</h1>
      </div>

      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            const isHighlight = 'highlight' in item && item.highlight;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-4 py-2 rounded-lg transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-600'
                      : isHighlight
                      ? 'bg-gradient-to-r from-purple-50 to-pink-50 text-purple-600 hover:from-purple-100 hover:to-pink-100 border border-purple-200'
                      : 'text-gray-600 hover:bg-gray-100'
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 px-4 py-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-medium">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.name}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-2 w-full text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <LogOut className="w-5 h-5" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
