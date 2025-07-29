"use client"

import type { ReactNode } from "react"
import {Link, useLocation, useNavigate} from "react-router"
import { LayoutDashboard, Activity, User, LogOut, Menu, Users, Server, ShieldCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import {removeToken} from "@/lib/auth";

interface MainLayoutProps {
  children: ReactNode
}

interface User {
  id: string,
  name: string,
  role: "admin" | "operator",
  createdAt: string
  email: string
  isSuperuser: boolean
}

export default function MainLayout({ children }: MainLayoutProps) {
  const router = useNavigate()
  const pathname = useLocation().pathname

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Devices", href: "/devices", icon: Server },
    { name: "Groups", href: "/groups", icon: Users },
    { name: "Executions", href: "/executions", icon: Activity },
    // { name: "Settings", href: "/settings", icon: Settings },
    { name: "Profile", href: "/profile", icon: User },
  ]

  const userData = localStorage.getItem("user")
  if (userData) {
    const user: User = JSON.parse(userData)
    if (user.isSuperuser) navigation.push({ name: "Superuser", href: "/admin", icon: ShieldCheck })
  }

  const logout = () => {
    removeToken()
    router("/login")
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* Top navigation bar */}
      <header className="sticky top-0 z-50 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6">
        <div className="flex items-center gap-2">
          <Link to="/dashboard" className="flex items-center gap-2 font-semibold">
            <span className="hidden md:inline-block">Formica</span>
          </Link>
        </div>

        {/* Mobile menu */}
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon" className="md:hidden">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left">
            <div className="grid gap-2 py-6">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-all hover:text-primary ${
                    pathname === item.href ? "bg-muted font-medium" : "text-muted-foreground"
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  {item.name}
                </Link>
              ))}
            </div>
          </SheetContent>
        </Sheet>

        {/* Desktop navigation */}
        <nav className="hidden md:flex md:flex-1 md:items-center md:gap-4 md:px-4">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-all hover:text-primary ${
                pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href))
                  ? "bg-muted font-medium"
                  : "text-muted-foreground"
              }`}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </Link>
          ))}
        </nav>

        {/* User menu */}
        <div className="ml-auto flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full">
                <img
                  src="/placeholder.svg?height=32&width=32"
                  alt="Avatar"
                  className="rounded-full"
                  height="32"
                  width="32"
                />
                <span className="sr-only">Toggle user menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link to="/profile">
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">{children}</main>
    </div>
  )
}
